"""Pydantic v2 models — single source of truth for the AI agent layer.

These models define the I/O contract between Member 3 (AI Agent) and
Member 2 (Back-End / FastAPI).  Member 2 imports directly from this
module to avoid schema drift (Gate G1 alignment).

Conventions:
    * All enums are ``str`` enums so they serialize cleanly to JSON.
    * Every model uses ``model_config = ConfigDict(extra="forbid")``
      to reject unexpected fields early.
    * Field names use snake_case throughout (JSON schema auto-generated
      for Member 1's typed client via FastAPI OpenAPI).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────


class TaskType(str, Enum):
    """Cognitive task the agent must perform (Section J)."""

    GENERATE_QUESTION = "generate_question"
    GENERATE_FOLLOWUP = "generate_followup"
    SCORE_ANSWER = "score_answer"
    SYNTHESIZE_FEEDBACK = "synthesize_feedback"
    SUMMARIZE = "summarize"


class QuestionType(str, Enum):
    """Question type taxonomy (Section C).

    Every generated question must be labelled with one of these.
    """

    CHALLENGE = "challenge"  # push back on a claim or assumption
    EXPAND = "expand"        # deepen into a specific technical detail
    COMPARE = "compare"      # contrast two technologies / approaches
    APPLY = "apply"          # scenario / hypothetical from cohort concepts
    TEACH = "teach"          # explain as if teaching a junior
    META = "meta"            # trade-offs, decision rationale, learning process


class Persona(str, Enum):
    """Persona variants (Section I)."""

    HIRING_MANAGER = "hiring_manager"
    SENIOR_ENGINEER = "senior_engineer"
    STAFF_ENGINEER = "staff_engineer"


class SpeakerRole(str, Enum):
    """Who said a conversation turn."""

    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"


class EvidenceSignal(str, Enum):
    """Strength label for an evidence-log entry."""

    STRONG = "strong"
    WEAK = "weak"
    MIXED = "mixed"


# ──────────────────────────────────────────────────────────────
# Shared data models
# ──────────────────────────────────────────────────────────────


class _Strict(BaseModel):
    """Base that forbids extra fields."""

    model_config = ConfigDict(extra="forbid")


class CurriculumDay(_Strict):
    """One day in the 31-day curriculum (from curriculum.json)."""

    day_id: str = Field(..., description="e.g. 'day_14'")
    title: str
    topics: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class CandidateProfile(_Strict):
    """Candidate progress data (from candidate_profiles.json)."""

    candidate_id: str
    completed_missions: list[str] = Field(default_factory=list)
    skipped_topics: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


class ConversationTurn(_Strict):
    """One turn in the interview conversation."""

    role: SpeakerRole
    content: str
    turn: int = Field(0, ge=0, description="0 = synthetic (e.g. summary) turn")


class EvidenceEntry(_Strict):
    """An evidence-log entry accumulated during the interview."""

    topic: str
    signal: EvidenceSignal
    evidence: str


class SessionMetadata(_Strict):
    """Live state tracked across turns (Section J session_metadata)."""

    session_id: str | None = Field(default=None, description="persisted by backend")
    turn_count: int = Field(0, ge=0)
    covered_days: list[str] = Field(default_factory=list)
    current_persona: Persona | None = None
    question_types_used: list[QuestionType] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Agent I/O envelope  (Section J)
# ──────────────────────────────────────────────────────────────


class AgentRequest(_Strict):
    """What the backend sends to ``agent.pipeline.run_agent``."""

    task: TaskType
    candidate_profile: CandidateProfile
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    session_metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    evidence_log: list[EvidenceEntry] = Field(default_factory=list)


class QuestionOutput(_Strict):
    """LLM output for generate_question / generate_followup.

    ``target_day`` is required for generate_question; follow-ups
    (Section I follow-up schema) omit it and use references_claim.
    """

    question: str
    target_day: str = Field(
        default="", description="e.g. 'day_12' — empty for follow-ups"
    )
    question_type: QuestionType
    persona: Persona | None = None
    references_claim: str | None = Field(
        default=None,
        description="For follow-ups: the specific claim from the last answer",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    validation_passed: bool = True


class SummaryOutput(_Strict):
    """LLM output for summarize."""

    summary: str


class AnswerScore(_Strict):
    """LLM output for score_answer: evaluate the candidate's LAST answer.

    ``score`` is 0-10.  ``strengths``/``gaps`` refer to what was just said
    (the transcript is full, but scoring focuses on the last turn).
    """

    score: float = Field(ge=0.0, le=10.0)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    suggested_focus: str | None = Field(
        default=None,
        description="One actionable direction for the follow-up question",
    )


class FeedbackStrength(_Strict):
    """A single strength claim in the feedback report."""

    claim: str
    citation: str = Field(
        default="",
        description=(
            "Verbatim quote from transcript supporting the claim. "
            "Must be non-empty unless is_partial=True (failure fallback)."
        ),
    )
    day_reference: str | None = None


class FeedbackGrowthArea(_Strict):
    """A single growth-area claim in the feedback report."""

    claim: str
    citation: str = Field(
        default="",
        description=(
            "Verbatim quote from transcript supporting the claim. "
            "Must be non-empty unless is_partial=True (failure fallback)."
        ),
    )
    day_reference: str | None = None
    suggested_resource: str | None = None


class FeedbackReport(_Strict):
    """Structured feedback — matches FeedbackReport Pydantic model (Section E).

    Every claim must include a ``citation`` that exists verbatim in the
    transcript (evidence anchoring ≥ 90 %).
    """

    readiness_score: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="0-10 readiness; null when partial/feedback failed",
    )
    strengths: list[FeedbackStrength] = Field(default_factory=list)
    growth_areas: list[FeedbackGrowthArea] = Field(default_factory=list)
    overall_summary: str = ""
    is_partial: bool = False
    disclaimer: str | None = None


class AgentOutput(_Strict):
    """What ``run_agent`` returns to the backend (Section J output schema)."""

    task: TaskType
    output: QuestionOutput | SummaryOutput | FeedbackReport | AnswerScore
    fallback_used: bool = False
    latency_ms: int = 0
    validation_passed: bool = True
    failure_reasons: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Fallback / template helpers
# ──────────────────────────────────────────────────────────────


def template_feedback_failure(covered_days: list[str] | None = None) -> FeedbackReport:
    """Return the partial feedback template when synthesis fails (Section G)."""
    days = ", ".join(covered_days) if covered_days else "your cohort materials"
    return FeedbackReport(
        readiness_score=None,
        strengths=[
            FeedbackStrength(
                claim="Interview completed. Detailed analysis unavailable due to technical issue."
            )
        ],
        growth_areas=[
            FeedbackGrowthArea(claim=f"Review your cohort materials for Days {days}.")
        ],
        is_partial=True,
        disclaimer=(
            "We encountered an issue generating detailed feedback. "
            "Please consult your instructor."
        ),
    )


# ──────────────────────────────────────────────────────────────
# JSON-schema export (for Member 1 / Member 2 codegen)
# ──────────────────────────────────────────────────────────────


def export_schemas(path: str | None = None) -> dict[str, Any]:
    """Return a dict of JSON schemas for all public models.

    If *path* is given, also write to that file.  Useful for Member 1
    to generate a typed API client without running Python.
    """
    models = [
        AgentRequest,
        AgentOutput,
        QuestionOutput,
        SummaryOutput,
        FeedbackReport,
        FeedbackStrength,
        FeedbackGrowthArea,
        CandidateProfile,
        CurriculumDay,
        ConversationTurn,
        EvidenceEntry,
        SessionMetadata,
    ]
    schemas = {m.__name__: m.model_json_schema() for m in models}
    if path:
        import json
        from pathlib import Path

        Path(path).write_text(
            json.dumps(schemas, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return schemas
