"""Context assembly & conversation windowing (Section F, Stage 1).

Assembles the full LLM context for every task:
* Windows the history (if > 6 turns, keep the last ``keep_recent`` turns —
  a pre-computed summary may be prepended; summarization itself happens in
  Feature 11 via the pipeline).
* Builds candidate profile + curriculum context (uncovered days).
* Runs the disallowed-topic guardrail pre-check.
* Renders system + user prompts via the Jinja2 prompt library (Feature 4).

Output is an :class:`AssembledContext` whose ``messages`` property yields
OpenAI-style chat messages for the LLM client.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from agent.config import settings
from agent.data.candidate import get_uncovered_days
from agent.data.curriculum import load_curriculum
from agent.prompts import render_system, render_user
from agent.schemas import (
    AgentRequest,
    ConversationTurn,
    Persona,
    TaskType,
)

# Topics that must never appear in context (guardrail pre-check).
DISALLOWED_TOPICS: tuple[str, ...] = (
    "forbidden",
    "illegal activity",
    "weapons",
    "weapon",
    "harm",
    "kill",
)


@dataclass
class AssembledContext:
    """Everything the inference pipeline needs to call the LLM."""

    system_prompt: str
    user_prompt: str
    uncovered_days: list[str]
    curriculum_context: str
    windowed_turns: list[ConversationTurn] = field(default_factory=list)
    used_summary: bool = False
    summary: str | None = None
    current_persona: Persona | None = None

    @property
    def messages(self) -> list[dict]:
        """OpenAI-style chat messages: [{"role": "system", ...}, {"role": "user", ...}]."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]


# ──────────────────────────────────────────────────────────────
# Windowing
# ──────────────────────────────────────────────────────────────


def window_history(
    history: list[ConversationTurn],
    summary: str | None = None,
) -> tuple[list[ConversationTurn], bool]:
    """Trim history to the context window.

    If ``len(history) > settings.context_window_turn_threshold`` (6), keep
    only the last ``context_window_keep_recent`` (4) turns.  When a
    pre-computed *summary* is supplied, it is prepended as a synthetic turn.
    Returns (windowed_history, used_summary).
    """
    if len(history) <= settings.context_window_turn_threshold:
        return list(history), False
    keep = settings.context_window_keep_recent
    windowed = list(history[-keep:])
    if summary:
        windowed = [
            ConversationTurn(
                role="interviewer",
                turn=0,
                content=f"[Summary of earlier turns] {summary}",
            )
        ] + windowed
    return windowed, bool(summary)


# ──────────────────────────────────────────────────────────────
# Curriculum context rendering
# ──────────────────────────────────────────────────────────────


def build_curriculum_context(day_ids: list[str], max_days: int = 5) -> str:
    """Render a compact curriculum snapshot for up to *max_days* day IDs."""
    curriculum = load_curriculum()
    lines = []
    for day_id in day_ids[:max_days]:
        day = curriculum.get(day_id)
        if day is None:
            continue
        objectives = "; ".join(day.learning_objectives)
        lines.append(
            f"- {day_id} ({day.title}): {objectives} | tools: {', '.join(day.tools)}"
        )
    return "\n".join(lines) if lines else "(no curriculum context available)"


# ──────────────────────────────────────────────────────────────
# Guardrails
# ──────────────────────────────────────────────────────────────


def guardrail_check(
    text: str, disallowed: tuple[str, ...] = DISALLOWED_TOPICS
) -> list[str]:
    """Return the disallowed topics present in *text* ([] means pass)."""
    lowered = text.lower()
    return [topic for topic in disallowed if topic.lower() in lowered]


def assert_guardrails(*texts: str) -> list[str]:
    """Combine guardrail flags across several text fragments."""
    hits: list[str] = []
    for text in texts:
        hits.extend(t for t in guardrail_check(text) if t not in hits)
    return hits


# ──────────────────────────────────────────────────────────────
# Assembly
# ──────────────────────────────────────────────────────────────


def _history_dicts(turns: list[ConversationTurn]) -> list[dict]:
    return [
        {"role": t.role.value, "content": t.content, "turn": t.turn} for t in turns
    ]


def _profile_dict(profile) -> dict:
    return {
        "candidate_id": profile.candidate_id,
        "completed_days": list(profile.completed_missions),
        "skipped_topics": list(profile.skipped_topics),
        "tools_used": list(profile.tools_used),
    }


def assemble_context(
    request: AgentRequest,
    *,
    summary: str | None = None,
    overwrite_persona: Persona | None = None,
) -> AssembledContext:
    """Assemble the complete LLM context for *request* (Section F Stage 1).

    Uses the request's own candidate profile and session metadata, so it
    works with live data pushed by Member 2, not only JSON fixtures:
    just the prompt assembly here; the LLM call happens later in the
    inference pipeline.
    """
    profile_dict = _profile_dict(request.candidate_profile)

    uncovered = get_uncovered_days(
        request.candidate_profile,
        covered_days=request.session_metadata.covered_days,
    )

    windowed, used_summary = window_history(request.conversation_history, summary)
    history_dicts = _history_dicts(windowed)

    persona = (
        Persona(overwrite_persona)
        if overwrite_persona
        else (
            Persona(request.session_metadata.current_persona)
            if request.session_metadata.current_persona
            else Persona.SENIOR_ENGINEER
        )
    )

    recent_qtypes = [
        t.value if hasattr(t, "value") else str(t)
        for t in request.session_metadata.question_types_used
    ]

    curriculum_days = list(request.session_metadata.covered_days) + uncovered
    curriculum_context = build_curriculum_context(curriculum_days)

    task = request.task
    if task == TaskType.GENERATE_QUESTION:
        user_prompt = render_user(
            "question_generation",
            profile=profile_dict,
            curriculum_context=curriculum_context,
            history=history_dicts,
            recent_question_types=", ".join(recent_qtypes),
            taxonomy_text="challenge, expand, compare, apply, teach, meta",
        )
    elif task == TaskType.GENERATE_FOLLOWUP:
        last_answer = (
            request.conversation_history[-1].content
            if request.conversation_history
            else ""
        )
        user_prompt = render_user(
            "followup_generation",
            last_answer=last_answer,
            history=history_dicts,
            recent_question_types=", ".join(recent_qtypes),
            evidence_log=[e.model_dump() for e in request.evidence_log],
        )
    elif task == TaskType.SYNTHESIZE_FEEDBACK:
        user_prompt = render_user(
            "feedback_synthesis",
            transcript=history_dicts,
            evidence_log=[e.model_dump() for e in request.evidence_log],
        )
    elif task == TaskType.SUMMARIZE:
        user_prompt = render_user("summarize", history=history_dicts)
    elif task == TaskType.SCORE_ANSWER:
        user_prompt = render_user(
            "score_answer",
            history=history_dicts,
            profile=profile_dict,
        )
    else:
        raise ValueError(f"Unknown task: {task}")

    system_prompt = render_system(persona.value)

    return AssembledContext(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        uncovered_days=uncovered,
        curriculum_context=curriculum_context,
        windowed_turns=windowed,
        used_summary=used_summary,
        summary=summary,
        current_persona=persona,
    )