"""Question type taxonomy + diversity enforcement (Sections C, E).

Maintains the ``recent_question_types`` queue (last 3) and enforces:
    * No repeated type within 2 turns.
    * At least 4 distinct types per interview (target metric).

The queue is a small pure-Python wrapper so the backend can persist it
in ``SessionMetadata.question_types_used`` between turns.
"""
from __future__ import annotations

from agent.config import settings
from agent.schemas import QuestionType

# Question-type descriptor strings for prompt injection (Section C).
TYPE_GUIDE: dict[QuestionType, str] = {
    QuestionType.CHALLENGE: (
        "challenge: push back on a claim or assumption the candidate made"
    ),
    QuestionType.EXPAND: (
        "expand: deepen into a specific technical detail of the previous answer"
    ),
    QuestionType.COMPARE: (
        "compare: ask the candidate to contrast two technologies or approaches"
    ),
    QuestionType.APPLY: (
        "apply: pose a scenario or hypothetical based on cohort concepts"
    ),
    QuestionType.TEACH: (
        "teach: ask the candidate to explain a concept as if teaching a junior"
    ),
    QuestionType.META: (
        "meta: ask about trade-offs, decision rationale, or learning process"
    ),
}


class QuestionTypeQueue:
    """Tracks recent question types and enforces the diversity rule.

    Params:
        history: recent types (oldest first), typically from
            ``SessionMetadata.question_types_used`` tail.
        window: how many recent types to retain for the diversity check.
    """

    def __init__(
        self,
        history: list[QuestionType] | list[str] | None = None,
        window: int | None = None,
    ) -> None:
        self.window = window if window else settings.max_recent_question_types
        # Full session history (for the '>= 4 distinct types' metric).
        self._all: list[QuestionType] = []
        # Rolling window of recent types (for the 'no repeat within 2' rule).
        self._recent: list[QuestionType] = []
        for item in history or []:
            self.record(item)

    def record(self, qtype: QuestionType | str) -> None:
        """Record that a question of *qtype* was asked this session."""
        qtype = QuestionType(qtype) if isinstance(qtype, str) else qtype
        self._all.append(qtype)
        self._recent.append(qtype)
        if len(self._recent) > self.window:
            self._recent.pop(0)

    @property
    def recent(self) -> list[QuestionType]:
        """The rolling window of recent question types (newest last)."""
        return list(self._recent)

    def is_allowed(self, qtype: QuestionType | str) -> bool:
        """True if a question of *qtype* may be asked now.

        Rule: no repeated type within 2 turns, i.e. the type must not
        appear among the last ``min(2, len(recent))`` entries.
        """
        qtype = QuestionType(qtype) if isinstance(qtype, str) else qtype
        last_two = self._recent[-2:]
        return qtype not in last_two

    def forbidden_types(self) -> list[QuestionType]:
        """Types that would violate the diversity rule right now (in order)."""
        return list(dict.fromkeys(self._recent[-2:]))

    def distinct_count(self) -> int:
        """Number of distinct types used across the whole session (target ≥ 4)."""
        return len(set(self._all))

    def diversity_satisfied(self) -> bool:
        """True once ≥ 4 distinct question types have been used."""
        return self.distinct_count() >= settings.min_distinct_types_per_interview

    def as_list(self) -> list[str]:
        """Serializable form for SessionMetadata.question_types_used."""
        return [t.value for t in self._all]


def type_guide_text() -> str:
    """Plain-text taxonomy description for injection into system prompts."""
    return "\n".join(f"- {d}" for d in TYPE_GUIDE.values())


def should_generate_followup(
    latest_score: float | None,
    validation_passed: bool,
    skip_ratio: float,
) -> bool:
    """Deterministic follow-up trigger (Section I).

    Generates a follow-up when the candidate gave a high-quality answer
    (score >= ``settings.followup_score_threshold``), or when the
    candidate has skipped > 50 % of the curriculum (re-engage the
    under-visited topics).  Suppressed when the answer failed validation.
    """
    if not validation_passed:
        return False
    forced = skip_ratio > settings.followup_skip_forcing_ratio
    if forced:
        return True
    if latest_score is None:
        return False
    return latest_score >= settings.followup_score_threshold