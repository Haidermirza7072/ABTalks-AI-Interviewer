from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ErrorResponse,
    FeedbackResponse,
    InterviewSession,
    RespondRequest,
    RespondResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.data_loader import CANDIDATE_STORE
from app.services.llm_client import generate_feedback_report, generate_next_question
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

    # Generate initial first question
    first_q = await generate_next_question(
        session=session,
        candidate_profile=candidate_profile,
        candidate_answer=None,
    )
    session.turn_count = 1
    session.can_conclude = False

    await save_session(session)

    return StartInterviewResponse(
        session_id=session.session_id,
        first_question=first_q,
        turn_count=session.turn_count,
        can_conclude=session.can_conclude,
        covered_days=list(session.covered_days),
        current_persona=session.current_persona,
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

    # Generate next question via LLM / Fallback
    next_q = await generate_next_question(
        session=session,
        candidate_profile=candidate_profile,
        candidate_answer=payload.answer,
    )

    await save_session(session)

    return RespondResponse(
        next_question=next_q,
        turn_count=session.turn_count,
        can_conclude=session.can_conclude,
        covered_days=list(session.covered_days),
        current_persona=session.current_persona,
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
    report = await generate_feedback_report(session, is_partial=False)
    await save_session(session)

    return FeedbackResponse(
        readiness_score=report.readiness_score,
        strengths=report.strengths,
        growth_areas=report.growth_areas,
        communication_tips=report.communication_tips,
        evidence_citations=report.evidence_citations,
        is_partial=report.is_partial,
        disclaimer=report.disclaimer,
    )


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
    report = await generate_feedback_report(session, is_partial=True)
    await save_session(session)

    return FeedbackResponse(
        readiness_score=report.readiness_score,
        strengths=report.strengths,
        growth_areas=report.growth_areas,
        communication_tips=report.communication_tips,
        evidence_citations=report.evidence_citations,
        is_partial=True,
        disclaimer="Partial feedback generated upon candidate abort.",
    )
