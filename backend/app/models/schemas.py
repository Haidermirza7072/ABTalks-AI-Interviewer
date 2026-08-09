from datetime import datetime, timezone
from collections import deque
from typing import Any, Deque, Dict, List, Literal, Optional, Set
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


# Entity 1: CandidateProfile
class CandidateProfile(BaseModel):
    candidate_id: str
    completed_missions: List[str] = Field(default_factory=list)
    skipped_topics: List[str] = Field(default_factory=list)
    attempts: Dict[str, int] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    learning_signals: Dict[str, Any] = Field(default_factory=dict)


# Entity 2: CurriculumDay
class CurriculumDay(BaseModel):
    day_id: str
    title: str
    topics: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


# Entity 3: InterviewSession
class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str
    status: Literal["active", "completed", "aborted"] = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    turn_count: int = 0
    can_conclude: bool = False
    covered_days: Set[str] = Field(default_factory=set)
    current_persona: Literal["hiring_manager", "senior_engineer", "staff_engineer"] = "hiring_manager"
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)  # [{"role": "interviewer|candidate", "content": "..."}]
    evidence_log: List[Dict[str, Any]] = Field(default_factory=list)
    question_types_used: Deque[str] = Field(default_factory=lambda: deque(maxlen=3))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        """Custom dictionary serializer for session JSON persistence."""
        return {
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": self.turn_count,
            "can_conclude": self.can_conclude,
            "covered_days": list(self.covered_days),
            "current_persona": self.current_persona,
            "conversation_history": self.conversation_history,
            "evidence_log": self.evidence_log,
            "question_types_used": list(self.question_types_used),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewSession":
        """Reconstruct InterviewSession object from serialized dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data["created_at"]
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if isinstance(data["updated_at"], str)
            else data["updated_at"]
        )
        q_types = deque(data.get("question_types_used", []), maxlen=3)
        return cls(
            session_id=data["session_id"],
            candidate_id=data["candidate_id"],
            status=data.get("status", "active"),
            created_at=created_at,
            updated_at=updated_at,
            turn_count=data.get("turn_count", 0),
            can_conclude=data.get("can_conclude", False),
            covered_days=set(data.get("covered_days", [])),
            current_persona=data.get("current_persona", "hiring_manager"),
            conversation_history=data.get("conversation_history", []),
            evidence_log=data.get("evidence_log", []),
            question_types_used=q_types,
        )


# ──────────────────────────────────────────────────────────────
# Feedback sub-models (aligned with agent schemas)
# ──────────────────────────────────────────────────────────────

class FeedbackStrengthResponse(BaseModel):
    """A single strength claim in the feedback report."""
    claim: str
    citation: str = ""
    day_reference: Optional[str] = None


class FeedbackGrowthAreaResponse(BaseModel):
    """A single growth-area claim in the feedback report."""
    claim: str
    citation: str = ""
    day_reference: Optional[str] = None
    suggested_resource: Optional[str] = None


class AnswerScoreResponse(BaseModel):
    """Per-turn answer scoring result."""
    score: float = Field(ge=0.0, le=10.0)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    suggested_focus: Optional[str] = None


# Entity 4: FeedbackReport (kept for internal use / backward compat)
class FeedbackReport(BaseModel):
    readiness_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    strengths: List[FeedbackStrengthResponse] = Field(default_factory=list)
    growth_areas: List[FeedbackGrowthAreaResponse] = Field(default_factory=list)
    overall_summary: str = ""
    is_partial: bool = False
    disclaimer: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# API Request/Response Models
# ──────────────────────────────────────────────────────────────


class StartInterviewRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=50)


class StartInterviewResponse(BaseModel):
    session_id: str
    first_question: str
    question_type: Optional[str] = None      # from QuestionOutput
    target_day: Optional[str] = None         # from QuestionOutput
    turn_count: int
    can_conclude: bool
    covered_days: List[str]
    current_persona: str
    fallback_used: bool = False              # from AgentOutput


class RespondRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


class RespondResponse(BaseModel):
    next_question: str
    question_type: Optional[str] = None      # from QuestionOutput
    target_day: Optional[str] = None         # from QuestionOutput
    turn_count: int
    can_conclude: bool
    covered_days: List[str]
    current_persona: str
    fallback_used: bool = False              # from AgentOutput
    answer_score: Optional[AnswerScoreResponse] = None  # per-turn score


class ScoreRequest(BaseModel):
    """Request body for the score endpoint (optional, can be empty)."""
    pass


class ScoreResponse(BaseModel):
    """Response for per-turn answer scoring."""
    score: float
    strengths: List[str]
    gaps: List[str]
    suggested_focus: Optional[str] = None
    fallback_used: bool = False


class FeedbackResponse(BaseModel):
    readiness_score: Optional[float] = None
    strengths: List[FeedbackStrengthResponse] = Field(default_factory=list)
    growth_areas: List[FeedbackGrowthAreaResponse] = Field(default_factory=list)
    overall_summary: str = ""
    is_partial: bool
    disclaimer: Optional[str] = None
    fallback_used: bool = False


# Standardized Error Response Schema
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    recoverable: bool = True
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
