"""Bridge between FastAPI backend sessions and the AI agent pipeline.

This module is the ONLY integration point between the backend's session/model
layer and ``agent.pipeline.run_agent``.  All AI work flows through here.

Functions:
    build_agent_request  — Convert InterviewSession → AgentRequest
    generate_question    — Question generation (replaces old llm_client logic)
    score_answer         — Per-turn answer scoring (new capability)
    generate_feedback    — Final feedback report synthesis
"""
from __future__ import annotations

import logging
from typing import Optional

from agent.pipeline import run_agent, update_session_after_run
from agent.schemas import (
    AgentOutput,
    AgentRequest,
    CandidateProfile as AgentCandidateProfile,
    ConversationTurn,
    EvidenceEntry,
    EvidenceSignal,
    Persona,
    QuestionType,
    SessionMetadata,
    SpeakerRole,
    TaskType,
)

from app.models.schemas import (
    CandidateProfile as BackendCandidateProfile,
    InterviewSession,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Schema translation helpers
# ──────────────────────────────────────────────────────────────


def _map_candidate_profile(
    backend_profile: BackendCandidateProfile,
) -> AgentCandidateProfile:
    """Convert backend CandidateProfile to agent CandidateProfile."""
    return AgentCandidateProfile(
        candidate_id=backend_profile.candidate_id,
        completed_missions=list(backend_profile.completed_missions),
        skipped_topics=list(backend_profile.skipped_topics),
        tools_used=list(backend_profile.tools_used),
    )


def _map_conversation_history(
    history: list[dict[str, str]],
) -> list[ConversationTurn]:
    """Convert backend conversation history dicts to ConversationTurn objects."""
    turns: list[ConversationTurn] = []
    for i, entry in enumerate(history, start=1):
        role_str = entry.get("role", "candidate")
        # Map backend role strings to agent SpeakerRole
        if role_str in ("interviewer", "assistant", "system"):
            role = SpeakerRole.INTERVIEWER
        else:
            role = SpeakerRole.CANDIDATE
        turns.append(
            ConversationTurn(
                role=role,
                content=entry.get("content", ""),
                turn=i,
            )
        )
    return turns


def _map_evidence_log(evidence_log: list[dict]) -> list[EvidenceEntry]:
    """Convert backend evidence log dicts to EvidenceEntry objects."""
    entries: list[EvidenceEntry] = []
    for entry in evidence_log:
        signal_str = entry.get("signal", "mixed")
        try:
            signal = EvidenceSignal(signal_str)
        except ValueError:
            signal = EvidenceSignal.MIXED
        entries.append(
            EvidenceEntry(
                topic=entry.get("topic", "general"),
                signal=signal,
                evidence=entry.get("evidence", ""),
            )
        )
    return entries


def _map_persona(persona_str: str) -> Optional[Persona]:
    """Convert backend persona string to agent Persona enum."""
    try:
        return Persona(persona_str)
    except ValueError:
        return Persona.SENIOR_ENGINEER


def _map_question_types(qtypes) -> list[QuestionType]:
    """Convert backend question_types_used deque to agent QuestionType list."""
    result: list[QuestionType] = []
    for qt in qtypes:
        try:
            result.append(QuestionType(qt))
        except ValueError:
            pass  # skip unknown types
    return result


# ──────────────────────────────────────────────────────────────
# AgentRequest builder
# ──────────────────────────────────────────────────────────────


def build_agent_request(
    session: InterviewSession,
    candidate_profile: BackendCandidateProfile,
    task: TaskType,
) -> AgentRequest:
    """Convert backend session + profile into an AgentRequest for the pipeline."""
    return AgentRequest(
        task=task,
        candidate_profile=_map_candidate_profile(candidate_profile),
        conversation_history=_map_conversation_history(session.conversation_history),
        session_metadata=SessionMetadata(
            session_id=session.session_id,
            turn_count=session.turn_count,
            covered_days=list(session.covered_days),
            current_persona=_map_persona(session.current_persona),
            question_types_used=_map_question_types(session.question_types_used),
        ),
        evidence_log=_map_evidence_log(session.evidence_log),
    )


# ──────────────────────────────────────────────────────────────
# Public bridge functions
# ──────────────────────────────────────────────────────────────


async def generate_question(
    session: InterviewSession,
    candidate_profile: Optional[BackendCandidateProfile],
    candidate_answer: Optional[str] = None,
) -> AgentOutput:
    """Generate the next interview question via the agent pipeline.

    Replaces the old backend ``generate_next_question`` function.
    Returns the full AgentOutput so the router can extract richer metadata.
    """
    # Append candidate answer to conversation history (if provided)
    if candidate_answer:
        session.conversation_history.append(
            {"role": "candidate", "content": candidate_answer}
        )

    # Decide task: follow-up if turn_count >= 2 and there's a recent answer
    is_followup = session.turn_count >= 2 and candidate_answer is not None
    task = TaskType.GENERATE_FOLLOWUP if is_followup else TaskType.GENERATE_QUESTION

    # Build request and call the agent pipeline
    request = build_agent_request(session, candidate_profile, task)
    output: AgentOutput = await run_agent(request)

    # Update session state from the agent's output (diversity queue, covered days, persona)
    update_session_after_run(request, output)

    # Sync agent state changes back to the backend session
    meta = request.session_metadata
    session.covered_days = set(meta.covered_days)
    if meta.current_persona:
        persona_val = meta.current_persona
        if hasattr(persona_val, "value"):
            persona_val = persona_val.value
        session.current_persona = persona_val

    # Append the generated question to conversation history
    question_text = getattr(output.output, "question", str(output.output))
    session.conversation_history.append(
        {"role": "interviewer", "content": question_text}
    )

    # Track question type
    qtype = getattr(output.output, "question_type", None)
    if qtype is not None:
        qtype_str = qtype.value if hasattr(qtype, "value") else str(qtype)
        session.question_types_used.append(qtype_str)

    logger.info(
        f"Agent generated question for session {session.session_id} "
        f"(task={task.value}, fallback={output.fallback_used})"
    )
    return output


async def score_answer(
    session: InterviewSession,
    candidate_profile: Optional[BackendCandidateProfile],
) -> AgentOutput:
    """Score the candidate's last answer via the agent pipeline.

    New capability not previously available in the backend.
    """
    request = build_agent_request(session, candidate_profile, TaskType.SCORE_ANSWER)
    output: AgentOutput = await run_agent(request)
    logger.info(
        f"Agent scored answer for session {session.session_id} "
        f"(fallback={output.fallback_used})"
    )
    return output


async def generate_feedback(
    session: InterviewSession,
    candidate_profile: Optional[BackendCandidateProfile] = None,
    is_partial: bool = False,
) -> AgentOutput:
    """Generate the feedback report via the agent pipeline.

    Replaces the old backend ``generate_feedback_report`` function.
    """
    # Use a dummy profile if none provided (feedback primarily uses transcript)
    if candidate_profile is None:
        candidate_profile = BackendCandidateProfile(
            candidate_id=session.candidate_id,
        )

    request = build_agent_request(
        session, candidate_profile, TaskType.SYNTHESIZE_FEEDBACK
    )
    output: AgentOutput = await run_agent(request)
    logger.info(
        f"Agent generated feedback for session {session.session_id} "
        f"(partial={is_partial}, fallback={output.fallback_used})"
    )
    return output
