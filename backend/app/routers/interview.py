from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.schemas import (
    AnswerScoreResponse,
    ErrorResponse,
    FeedbackGrowthAreaResponse,
    FeedbackResponse,
    FeedbackStrengthResponse,
    InterviewSession,
    RespondRequest,
    RespondResponse,
    ScoreResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.data_loader import CANDIDATE_STORE
from app.services.agent_bridge import generate_question, generate_feedback, score_answer
from app.services.session_manager import get_session, save_session

router = APIRouter(prefix="/interview", tags=["Interview"])


def create_error_response(status_code: int, error_code: str, message: str, recoverable: bool = True):
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "recoverable": recoverable,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def _extract_question_metadata(agent_output):
    """Extract enriched metadata from an AgentOutput's QuestionOutput."""
    output = agent_output.output
    question_text = getattr(output, "question", str(output))
    question_type = getattr(output, "question_type", None)
    target_day = getattr(output, "target_day", None)

    if question_type and hasattr(question_type, "value"):
        question_type = question_type.value
    if question_type:
        question_type = str(question_type)

    return question_text, question_type, target_day


def _map_feedback_response(agent_output, is_partial: bool = False) -> FeedbackResponse:
    """Map agent FeedbackReport output to backend FeedbackResponse."""
    report = agent_output.output

    # Map strengths
    strengths = []
    for s in getattr(report, "strengths", []):
        strengths.append(FeedbackStrengthResponse(
            claim=getattr(s, "claim", str(s)),
            citation=getattr(s, "citation", ""),
            day_reference=getattr(s, "day_reference", None),
        ))

    # Map growth areas
    growth_areas = []
    for g in getattr(report, "growth_areas", []):
        growth_areas.append(FeedbackGrowthAreaResponse(
            claim=getattr(g, "claim", str(g)),
            citation=getattr(g, "citation", ""),
            day_reference=getattr(g, "day_reference", None),
            suggested_resource=getattr(g, "suggested_resource", None),
        ))

    return FeedbackResponse(
        readiness_score=getattr(report, "readiness_score", None),
        strengths=strengths,
        growth_areas=growth_areas,
        overall_summary=getattr(report, "overall_summary", ""),
        is_partial=getattr(report, "is_partial", is_partial),
        disclaimer=getattr(report, "disclaimer", None),
        fallback_used=agent_output.fallback_used,
    )


@router.post(
    "/start",
    response_model=StartInterviewResponse,
    summary="Initialize interview session",
    responses={
        404: {"model": ErrorResponse, "description": "Candidate profile not found"},
        422: {"description": "Validation error"},
    },
)
async def start_interview(payload: StartInterviewRequest):
    """Initialize a new interview session for a valid candidate."""
    if payload.candidate_id not in CANDIDATE_STORE:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CANDIDATE_NOT_FOUND",
            message="Candidate profile not found.",
        )

    candidate_profile = CANDIDATE_STORE[payload.candidate_id]
    session = InterviewSession(candidate_id=payload.candidate_id)

    # Generate initial first question via the agent pipeline
    agent_output = await generate_question(
        session=session,
        candidate_profile=candidate_profile,
        candidate_answer=None,
    )
    session.turn_count = 1
    session.can_conclude = False

    await save_session(session)

    first_q, question_type, target_day = _extract_question_metadata(agent_output)

    return StartInterviewResponse(
        session_id=session.session_id,
        first_question=first_q,
        question_type=question_type,
        target_day=target_day or "",
        turn_count=session.turn_count,
        can_conclude=session.can_conclude,
        covered_days=list(session.covered_days),
        current_persona=session.current_persona,
        fallback_used=agent_output.fallback_used,
    )


@router.post(
    "/{session_id}/respond",
    response_model=RespondResponse,
    summary="Submit answer and receive next question",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def respond_interview(session_id: str, payload: RespondRequest):
    """Submit candidate answer and generate the next interview question."""
    session = get_session(session_id)
    if not session or session.status != "active":
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            message="The interview session has expired or does not exist.",
        )

    candidate_profile = CANDIDATE_STORE.get(session.candidate_id)

    # Process turn
    session.turn_count += 1
    if session.turn_count >= 3:
        session.can_conclude = True

    # Generate next question via the agent pipeline
    agent_output = await generate_question(
        session=session,
        candidate_profile=candidate_profile,
        candidate_answer=payload.answer,
    )

    # Optionally score the submitted answer
    answer_score_resp = None
    try:
        score_output = await score_answer(
            session=session,
            candidate_profile=candidate_profile,
        )
        score_data = score_output.output
        answer_score_resp = AnswerScoreResponse(
            score=getattr(score_data, "score", 5.0),
            strengths=getattr(score_data, "strengths", []),
            gaps=getattr(score_data, "gaps", []),
            suggested_focus=getattr(score_data, "suggested_focus", None),
        )
    except Exception:
        pass  # scoring is optional, don't block the interview

    await save_session(session)

    next_q, question_type, target_day = _extract_question_metadata(agent_output)

    return RespondResponse(
        next_question=next_q,
        question_type=question_type,
        target_day=target_day or "",
        turn_count=session.turn_count,
        can_conclude=session.can_conclude,
        covered_days=list(session.covered_days),
        current_persona=session.current_persona,
        fallback_used=agent_output.fallback_used,
        answer_score=answer_score_resp,
    )


@router.post(
    "/{session_id}/score",
    response_model=ScoreResponse,
    summary="Score the candidate's last answer",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def score_last_answer(session_id: str):
    """Score the candidate's most recent answer without advancing the interview."""
    session = get_session(session_id)
    if not session:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            message="The interview session has expired or does not exist.",
        )

    candidate_profile = CANDIDATE_STORE.get(session.candidate_id)
    score_output = await score_answer(
        session=session,
        candidate_profile=candidate_profile,
    )
    score_data = score_output.output

    return ScoreResponse(
        score=getattr(score_data, "score", 5.0),
        strengths=getattr(score_data, "strengths", []),
        gaps=getattr(score_data, "gaps", []),
        suggested_focus=getattr(score_data, "suggested_focus", None),
        fallback_used=score_output.fallback_used,
    )


@router.post(
    "/{session_id}/feedback",
    response_model=FeedbackResponse,
    summary="Generate final interview feedback report",
    responses={
        400: {"model": ErrorResponse, "description": "Interview too short"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def get_feedback(session_id: str):
    """Conclude active interview and generate synthesized feedback report."""
    session = get_session(session_id)
    if not session:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            message="The interview session has expired or does not exist.",
        )

    if session.turn_count < 1:
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INTERVIEW_TOO_SHORT",
            message="Interview session must have at least 1 turn completed before generating feedback.",
        )

    session.status = "completed"
    candidate_profile = CANDIDATE_STORE.get(session.candidate_id)
    agent_output = await generate_feedback(session, candidate_profile, is_partial=False)
    await save_session(session)

    return _map_feedback_response(agent_output, is_partial=False)


@router.post(
    "/{session_id}/abort",
    response_model=FeedbackResponse,
    summary="Early termination of interview",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def abort_interview(session_id: str):
    """Abort an active interview early and return partial feedback report."""
    session = get_session(session_id)
    if not session:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            message="The interview session has expired or does not exist.",
        )

    session.status = "aborted"
    candidate_profile = CANDIDATE_STORE.get(session.candidate_id)
    agent_output = await generate_feedback(session, candidate_profile, is_partial=True)
    await save_session(session)

    response = _map_feedback_response(agent_output, is_partial=True)
    response.disclaimer = response.disclaimer or "Partial feedback generated upon candidate abort."
    return response
