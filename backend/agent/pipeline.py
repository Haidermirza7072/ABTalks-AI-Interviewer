"""Inference pipeline orchestrator — ``run_agent`` (Sections B, F, G, H).

Single async entry point consumed by Member 2's FastAPI service.

Stages (per call):
    1. Pre-process: guardrail pre-check + context assembly (F5).
    2. Infer: call OpenRouter (primary model, JSON mode) with per-task
       sampling config (F6).  Timeout/5xx triggers fallback.
    3. Post-process: JSON parse -> schema validation -> content
       validation -> optional semantic relevance (F7).
    4. Fallback: one stricter retry; then the fallback bank (F8) or the
       partial-feedback template (Section G).

Each run is logged to the JSONL session log (F14) for the eval suite.

The public API for Member 2:
    from agent.pipeline import run_agent
    result = await run_agent(request)      # -> AgentOutput
"""
from __future__ import annotations

import time
from typing import Any

from agent.config import settings
from agent.context import (
    assemble_context,
    assert_guardrails,
    window_history,
)
import agent.logging as logging
from agent.fallback import FallbackBank
from agent.llm_client import LLMClient, LLMUnavailableError, _extract_json
from agent.persona import PersonaManager
from agent.schemas import (
    AgentOutput,
    AgentRequest,
    AnswerScore,
    FeedbackReport,
    Persona,
    QuestionOutput,
    SummaryOutput,
    TaskType,
    template_feedback_failure,
)
from agent.taxonomy import QuestionTypeQueue
from agent.validation import validate_llm_output

# Retry-once-with-stricter-instruction suffix (Section F Stage 4).
_RETRY_HINT = (
    "Simplify. Focus only on the requested schema and the candidate's "
    "actual answer. Output strict JSON only."
)


class PipelineError(RuntimeError):
    """Unrecoverable pipeline failure (empty fallback bank, etc.)."""


def _task_config(task: TaskType):
    """Per-task model config (Section D)."""
    return {
        TaskType.GENERATE_QUESTION: settings.question_config,
        TaskType.GENERATE_FOLLOWUP: settings.followup_config,
        TaskType.SYNTHESIZE_FEEDBACK: settings.feedback_config,
        TaskType.SUMMARIZE: settings.summarize_config,
        TaskType.SCORE_ANSWER: settings.score_config,
    }[task]


def _transcript_lines(history) -> list[str]:
    """Flatten conversation turns to text lines for citation checks."""
    return [t.content for t in history]


class AgentPipeline:
    """Holds client + bank, so tests can inject mocks.

    ``check_relevance`` — when True, semantic relevance to the target
    day's objectives is computed (embedding call) and treated as a
    validation input; used by the eval suite.  Off by default to keep
    the interview latency low (Section F Stage 3 lists relevance as a
    measured metric, not a hard gate).
    """

    def __init__(
        self,
        client: LLMClient | None = None,
        bank: FallbackBank | None = None,
        logger=None,
        check_relevance: bool = False,
    ) -> None:
        self.client = client or LLMClient()
        self.bank = bank or FallbackBank()
        self.logger = logger or logging.log_run
        self.check_relevance = check_relevance

    def _log(
        self,
        request: AgentRequest,
        out: AgentOutput,
        *,
        expected_type: str | None = None,
        relevance: float | None = None,
        failure_reasons: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Write one JSONL record per pipeline run (Section H)."""
        output = out.output
        actual_type = getattr(output, "question_type", None)
        if hasattr(actual_type, "value"):
            actual_type = actual_type.value
        try:
            self.logger(
                session_id=request.session_metadata.session_id
                if hasattr(request.session_metadata, "session_id")
                else "unknown-session",
                candidate_id=request.candidate_profile.candidate_id,
                task=out.task.value,
                question=getattr(output, "question", None),
                expected_type=expected_type,
                actual_type=str(actual_type) if actual_type else None,
                relevance_score=relevance,
                validation_passed=out.validation_passed,
                fallback_used=out.fallback_used,
                persona=getattr(out.output, "persona", None),
                latency_ms=out.latency_ms,
                failure_reasons=failure_reasons or [],
                extra=extra or {},
            )
        except Exception:
            pass  # logging must never break the interview flow

    # ──────────────────────────────────────────────────────────
    # Task runners (F11 summarize, F12 feedback, question/follow-up)
    # ──────────────────────────────────────────────────────────

    async def _summarize(self, request: AgentRequest) -> AgentOutput:
        """Summarize long histories (F11)."""
        start = time.perf_counter()
        ctx = assemble_context(request)
        try:
            raw = await self.client.chat_json(ctx.messages, settings.summarize_config)
        except LLMUnavailableError:
            raw = None
        result = validate_llm_output(TaskType.SUMMARIZE, raw)
        if not result.passed:
            return AgentOutput(
                task=TaskType.SUMMARIZE,
                output=SummaryOutput(
                    summary="Conversation too long to summarize reliably."
                ),
                fallback_used=True,
                latency_ms=int((time.perf_counter() - start) * 1000),
                validation_passed=False,
                failure_reasons=result.reasons,
            )
        return AgentOutput(
            task=TaskType.SUMMARIZE,
            output=result.parsed,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    async def _score(self, request: AgentRequest) -> AgentOutput:
        """Score the candidate's LAST answer (per-turn feedback, Section I)."""
        start = time.perf_counter()
        ctx = assemble_context(request)
        try:
            raw = await self.client.chat_json(ctx.messages, settings.score_config)
        except LLMUnavailableError:
            raw = None
        result = validate_llm_output(TaskType.SCORE_ANSWER, raw)
        if result.passed:
            return AgentOutput(
                task=TaskType.SCORE_ANSWER,
                output=result.parsed,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        # Never block the interview on scoring: neutral fallback score.
        return AgentOutput(
            task=TaskType.SCORE_ANSWER,
            output=AnswerScore(
                score=5.0,
                strengths=[],
                gaps=["Could not evaluate the answer right now."],
            ),
            fallback_used=True,
            latency_ms=int((time.perf_counter() - start) * 1000),
            validation_passed=False,
            failure_reasons=result.reasons,
        )

    async def _feedback(self, request: AgentRequest) -> AgentOutput:
        """Synthesize a feedback report (F12, Section G template fallback)."""
        start = time.perf_counter()
        ctx = assemble_context(request)
        transcript = _transcript_lines(request.conversation_history)
        try:
            raw = await self.client.chat_json(ctx.messages, settings.feedback_config)
        except LLMUnavailableError:
            raw = None
        result = validate_llm_output(
            TaskType.SYNTHESIZE_FEEDBACK,
            raw,
            transcript=transcript,
        )
        if result.passed:
            return AgentOutput(
                task=TaskType.SYNTHESIZE_FEEDBACK,
                output=result.parsed,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        # Section G feedback fallback template.
        covered = request.session_metadata.covered_days
        return AgentOutput(
            task=TaskType.SYNTHESIZE_FEEDBACK,
            output=template_feedback_failure(covered),
            fallback_used=True,
            latency_ms=int((time.perf_counter() - start) * 1000),
            validation_passed=False,
            failure_reasons=result.reasons,
        )

    async def _question(
        self, request: AgentRequest, *, is_followup: bool
    ) -> AgentOutput:
        """Generate a question or follow-up with retry + bank fallback."""
        start = time.perf_counter()
        task = (
            TaskType.GENERATE_FOLLOWUP if is_followup else TaskType.GENERATE_QUESTION
        )
        config = _task_config(task)
        recent_types = [
            t.value if hasattr(t, "value") else str(t)
            for t in request.session_metadata.question_types_used
        ]

        # ── Attempt 1 ────────────────────────────────────────
        ctx = assemble_context(request)
        try:
            raw = await self.client.chat_json(ctx.messages, config)
        except LLMUnavailableError:
            raw = None
        result = validate_llm_output(
            task, raw, recent_question_types=recent_types
        )
        if result.passed and self.check_relevance and not is_followup:
            # Section E: semantic relevance to the target day's objectives.
            from agent.data.curriculum import get_day
            from agent.eval.relevance import relevance_score

            day = get_day(result.parsed.target_day) if result.parsed.target_day else None
            if day is not None:
                score = await relevance_score(
                    self.client, result.parsed.question, day.learning_objectives
                )
                if score is not None and score < settings.relevance_threshold:
                    result.passed = False
                    result.add_failure(
                        f"semantic relevance {score:.3f} < {settings.relevance_threshold}"
                    )
                if hasattr(result, "relevance_score"):
                    result.relevance_score = score
        if result.passed:
            return self._question_ok(task, result.parsed, start)

        # ── Attempt 2: one stricter retry (Section F Stage 4) ─
        retry_user = ctx.user_prompt + "\n\n" + _RETRY_HINT
        retry_messages = [
            {"role": "system", "content": ctx.system_prompt},
            {"role": "user", "content": retry_user},
        ]
        try:
            raw2 = await self.client.chat_json(retry_messages, config)
        except LLMUnavailableError:
            raw2 = None
        result2 = validate_llm_output(task, raw2, recent_question_types=recent_types)
        if result2.passed:
            return self._question_ok(task, result2.parsed, start)

        # ── Fallback bank (Section G) ────────────────────────
        fallback_item = self._select_fallback(request, recent_types)
        out = QuestionOutput(
            question=fallback_item["question"],
            target_day=fallback_item.get("target_day", ""),
            question_type=fallback_item.get("question_type", "meta"),
            persona=fallback_item.get("persona"),
            validation_passed=True,
        )
        return AgentOutput(
            task=task,
            output=out,
            fallback_used=True,
            latency_ms=int((time.perf_counter() - start) * 1000),
            validation_passed=False,
            failure_reasons=result2.reasons or result.reasons,
        )

    @staticmethod
    def _question_ok(task: TaskType, parsed, start: float) -> AgentOutput:
        return AgentOutput(
            task=task,
            output=parsed,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    def _select_fallback(self, request: AgentRequest, recent_types: list[str]):
        """Section G priority: completed-uncovered, skipped, then general."""
        completed_uncovered = [
            d
            for d in request.candidate_profile.completed_missions
            if d not in request.session_metadata.covered_days
        ]
        skipped = list(request.candidate_profile.skipped_topics)
        item = self.bank.select(
            completed_uncovered=completed_uncovered, skipped=skipped
        )
        # Diversity guard: rotate if the chosen type repeats.
        if item["question_type"] in recent_types[-2:]:
            for day_id in (completed_uncovered + skipped):
                rotated = self.bank.rotate_for_day(day_id, {item["question"]})
                if rotated:
                    return rotated
        return item

    # ──────────────────────────────────────────────────────────
    # Orchestration
    # ──────────────────────────────────────────────────────────

    async def run(self, request: AgentRequest) -> AgentOutput:
        """Execute the 4-stage pipeline for *request*."""
        # Stage 1: guardrail pre-check over raw text inputs.
        texts = [
            request.candidate_profile.candidate_id,
            *(t.content for t in request.conversation_history),
        ]
        violations = assert_guardrails(*texts)
        if violations:
            raise PipelineError(
                f"Context contains disallowed topics: {', '.join(violations)}"
            )

        if request.task == TaskType.SUMMARIZE:
            out = await self._summarize(request)
        elif request.task == TaskType.SCORE_ANSWER:
            out = await self._score(request)
        elif request.task == TaskType.SYNTHESIZE_FEEDBACK:
            out = await self._feedback(request)
        elif request.task == TaskType.GENERATE_FOLLOWUP:
            out = await self._question(request, is_followup=True)
        elif request.task == TaskType.GENERATE_QUESTION:
            out = await self._question(request, is_followup=False)
        else:
            raise PipelineError(f"Unknown task: {request.task}")

        self._log(request, out, failure_reasons=out.failure_reasons)
        return out


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


_pipeline: AgentPipeline | None = None


def get_pipeline() -> AgentPipeline:
    """Process-wide singleton pipeline (client + bank cached)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AgentPipeline()
    return _pipeline


async def run_agent(request: AgentRequest) -> AgentOutput:
    """Awaitable entry point for Member 2's FastAPI endpoints.

    Usage:
        from agent.pipeline import run_agent
        from agent.schemas import AgentRequest
        result = await run_agent(AgentRequest.model_validate(payload))
    """
    return await get_pipeline().run(request)


def update_session_after_run(
    request: AgentRequest, output: AgentOutput
) -> None:
    """Mutate *request.session_metadata* with what just happened.

    The backend MUST call this after every run so that the diversity
    queue, covered-day tracking, and persona rotation stay correct
    (Sections C/J).  Skip for synthesize_feedback / summarize.
    """
    meta = request.session_metadata
    meta.turn_count += 1
    if output.task in (TaskType.GENERATE_QUESTION, TaskType.GENERATE_FOLLOWUP):
        qtype = getattr(output.output, "question_type", None)
        if qtype is not None:
            meta.question_types_used.append(qtype)
        day = getattr(output.output, "target_day", None)
        if day and day not in meta.covered_days:
            meta.covered_days.append(day)
    persona = getattr(output.output, "persona", None)
    if persona is not None:
        meta.current_persona = persona