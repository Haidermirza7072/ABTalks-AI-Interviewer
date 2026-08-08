"""Post-processing validation & guardrails (Section F Stage 3, Section E).

Runs after the LLM returns JSON:
1. Parse + Pydantic schema validation.
2. Content validation:
   - target_day exists in the curriculum
   - question_type is in the allowed taxonomy
   - no question-type repetition within the last 2 turns
   - feedback: every claim cites a verbatim transcript quote
     (evidence anchoring >= target)
3. Lightweight hallucination smoke check: factual keywords in the question
   are cross-checked against the curriculum fact surface.
4. Semantic relevance (cosine) is computed by ``agent.eval.relevance``
   (F13) and merged in by the pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from agent.config import settings
from agent.data.curriculum import is_valid_day, load_curriculum
from agent.schemas import (
    AnswerScore,
    FeedbackReport,
    QuestionOutput,
    QuestionType,
    SummaryOutput,
    TaskType,
)

# Clinically useful factual vocabulary from the cohort curriculum — used
# only for the lightweight hallucination warning (Section E).
_CURRICULUM_TERMS: tuple[str, ...] = (
    "vector", "embedding", "cosine similarity", "neural network",
    "gradient descent", "backpropagation", "chromadb", "pytorch",
    "langchain", "pandas", "sklearn", "fastapi", "lora",
    "retrieval-augmented", "prompt injection", "hybrid search",
)


@dataclass
class ValidationResult:
    """Outcome of validating one LLM output."""

    passed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    relevance_score: float | None = None
    confidence: float = 0.0
    parsed: QuestionOutput | SummaryOutput | "FeedbackReport" | None = None

    def add_failure(self, reason: str) -> None:
        self.passed = False
        self.reasons.append(reason)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "relevance_score": self.relevance_score,
        }


def _curriculum_fact_surface() -> str:
    """Lowcased concatenation of all curriculum text (for hallucination check)."""
    parts = []
    for day in load_curriculum().values():
        parts.extend(day.topics)
        parts.extend(day.learning_objectives)
        parts.extend(day.tools)
    return " ".join(parts).lower()


# ──────────────────────────────────────────────────────────────
# Stage 3a: schema validation
# ──────────────────────────────────────────────────────────────


def schema_validate(task: TaskType, raw: dict | None) -> ValidationResult:
    """Validate the parsed JSON dict against the Pydantic model for *task*.

    100 % schema compliance is the target for feedback; the pipeline falls
    back if this fails.
    """
    result = ValidationResult(passed=False)
    if raw is None:
        result.add_failure("LLM returned no parseable JSON")
        return result
    try:
        if task in (TaskType.GENERATE_QUESTION, TaskType.GENERATE_FOLLOWUP):
            result.parsed = QuestionOutput.model_validate(raw)
        elif task == TaskType.SYNTHESIZE_FEEDBACK:
            result.parsed = FeedbackReport.model_validate(raw)
        elif task == TaskType.SUMMARIZE:
            result.parsed = SummaryOutput.model_validate(raw)
        elif task == TaskType.SCORE_ANSWER:
            result.parsed = AnswerScore.model_validate(raw)
        else:
            result.add_failure(f"Unsupported task: {task}")
            return result
        result.passed = True
    except Exception as exc:  # pydantic.ValidationError
        result.add_failure(f"Schema validation failed: {exc}")
    return result


# ──────────────────────────────────────────────────────────────
# Stage 3b: content validation
# ──────────────────────────────────────────────────────────────


def content_validate(
    task: TaskType,
    parsed,
    *,
    recent_question_types: list[str] | None = None,
    transcript: list[str] | None = None,
) -> ValidationResult:
    """Content-level guardrails on an already-schema-validated output."""
    result = ValidationResult(passed=True, parsed=parsed)
    if isinstance(parsed, QuestionOutput):
        _validate_question(parsed, result, recent_question_types or [])
    elif isinstance(parsed, FeedbackReport):
        _validate_feedback(parsed, result, transcript or [])
    return result


def _validate_question(
    q: QuestionOutput, result: ValidationResult, recent: list[str]
) -> None:
    # target_day exists in curriculum (required only for question gen;
    # follow-ups omit it per the Section I follow-up schema)
    if q.target_day and not is_valid_day(q.target_day):
        result.add_failure(f"target_day '{q.target_day}' not in curriculum")

    # question_type in taxonomy (parsed as enum already, but double-check)
    try:
        QuestionType(q.question_type)
    except ValueError:
        result.add_failure(f"invalid question_type '{q.question_type}'")

    # diversity: no repeat within the last 2 turns
    recent_values = [str(t) for t in recent[-2:]]
    if q.question_type.value in recent_values:
        result.add_failure(
            f"question_type '{q.question_type.value}' repeats within 2 turns "
            f"(recent: {recent_values})"
        )

    # hallucination smoke check (warnings only; hard fail handled by pipeline)
    surface = _curriculum_fact_surface()
    lower_q = q.question.lower()
    for term in _CURRICULUM_TERMS:
        if term in lower_q and term not in surface:
            result.warnings.append(f"technical term '{term}' not grounded in curriculum")


def _validate_feedback(
    fb: FeedbackReport, result: ValidationResult, transcript: list[str]
) -> None:
    """Verify every strength/growth claim anchors to the transcript."""
    joined = "\n".join(transcript)
    anchored = 0
    total = 0
    for item in list(fb.strengths) + list(fb.growth_areas):
        total += 1
        if item.citation and item.citation in joined:
            anchored += 1
        else:
            if fb.is_partial:
                continue  # section-G template: no citations required, allow pass
            result.add_failure(
                f"citation not in transcript: {item.citation[:60]!r}"
                if item.citation else
                f"claim missing citation: {item.claim[:50]!r}"
            )
    if total and not fb.is_partial and anchored / total < settings.evidence_anchoring_target:
        result.add_failure(
            f"evidence anchoring {anchored}/{total} under "
            f"{settings.evidence_anchoring_target} target"
        )


# ──────────────────────────────────────────────────────────────
# Orchestration entry
# ──────────────────────────────────────────────────────────────


def validate_llm_output(
    task: TaskType,
    raw: dict | None,
    *,
    recent_question_types: list[str] | None = None,
    transcript: list[str] | None = None,
) -> ValidationResult:
    """Full post-processing: schema + content validation in one call."""
    schema_result = schema_validate(task, raw)
    if not schema_result.passed:
        return schema_result
    content = content_validate(
        task,
        schema_result.parsed,
        recent_question_types=recent_question_types,
        transcript=transcript,
    )
    return content