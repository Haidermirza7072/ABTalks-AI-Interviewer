"""Smoke test for F9 pipeline — mocked LLM client (offline).

Covers:
  1. Question generation happy path.
  2. Follow-up generation happy path.
  3. Schema-invalid LLM output -> stricter retry -> bank fallback.
  4. Feedback synthesis happy path.
  5. Feedback LLM failure -> partial template fallback.
  6. Summarize task.
  7. Guardrail pre-check raises PipelineError.
"""
import asyncio

from agent.fallback import FallbackBank
from agent.llm_client import LLMUnavailableError
from agent.pipeline import AgentPipeline, PipelineError
from agent.schemas import (
    EvidenceEntry,
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    SessionMetadata,
    TaskType,
)

PROFILE = CandidateProfile(
    candidate_id="cand_001_anxious_alex",
    completed_missions=["day_12", "day_13"],
    skipped_topics=["day_14"],
    tools_used=["ChromaDB"],
)
HISTORY = [
    ConversationTurn(role="interviewer", content="Tell me about your RAG project.", turn=1),
    ConversationTurn(role="candidate", content="I built it with ChromaDB.", turn=2),
]
EVIDENCE = [EvidenceEntry(topic="RAG", signal="strong", evidence="Explained retrieval")]


class FakeLLM:
    """Scripted chat_json responses: dict payloads or exceptions."""

    def __init__(self, responses: list) -> None:
        self.responses = responses
        self.calls = 0

    def _next(self):
        item = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item

    async def chat_json(self, messages, config, model=None):
        return self._next()


def make_request(task: str) -> AgentRequest:
    return AgentRequest(
        task=task,  # type: ignore[assignment]
        candidate_profile=PROFILE,
        conversation_history=HISTORY,
        session_metadata=SessionMetadata(
            turn_count=5, question_types_used=["challenge"]
        ),
        evidence_log=EVIDENCE,
    )


async def main() -> None:
    # 1. Question happy path
    llm = FakeLLM([
        {"question": "Why ChromaDB and cosine similarity for your RAG?", "target_day": "day_12",
         "question_type": "expand", "persona": "senior_engineer"},
    ])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("generate_question"))
    assert out.output.question.startswith("Why ChromaDB")
    assert not out.fallback_used and out.validation_passed
    print("1. Question happy path OK:", out.output.question[:40], "|", out.output.question_type.value)

    # 2. Follow-up happy path
    llm = FakeLLM([
        {"question": "Which part of ChromaDB worried you most?", "question_type": "expand",
         "references_claim": "ChromaDB"},
    ])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("generate_followup"))
    assert out.output.references_claim == "ChromaDB"
    print("2. Follow-up happy path OK:", out.output.question)

    # 3. Invalid LLM output twice -> bank fallback
    llm = FakeLLM([{"nonsense": 42}, {"garbage": True}])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("generate_question"))
    assert out.fallback_used
    assert out.output.question  # served from the bank
    assert out.output.target_day in ("day_12", "day_13")  # completed-uncovered priority
    print("3. Invalid output -> retry -> bank fallback OK:", out.output.target_day)

    # 4. Feedback happy path
    feedback_payload = {
        "readiness_score": 7.5,
        "strengths": [{"claim": "Clear RAG reasoning.", "citation": "I built it with ChromaDB."}],
        "growth_areas": [{"claim": "Probe vector trade-offs.", "citation": "I built it with ChromaDB."}],
        "overall_summary": "Solid.",
        "is_partial": False,
    }
    llm = FakeLLM([feedback_payload])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("synthesize_feedback"))
    assert out.output.is_partial is False and out.output.readiness_score == 7.5
    print("4. Feedback happy path OK: score", out.output.readiness_score)

    # 5. Feedback LLM failure -> partial template
    llm = FakeLLM([LLMUnavailableError("timeout")])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("synthesize_feedback"))
    assert out.fallback_used and out.output.is_partial and out.output.disclaimer
    print("5. Feedback failure -> partial template OK:", out.output.is_partial)

    # 6. Summarize
    llm = FakeLLM([{"summary": "Candidate solid on RAG, weak on vector trade-offs."}])
    out = await AgentPipeline(client=llm, bank=FallbackBank()).run(make_request("summarize"))
    assert "RAG" in out.output.summary
    print("6. Summarize OK:", out.output.summary[:50])

    # 7. Guardrail pre-flight
    bad = AgentRequest(
        task="generate_question", candidate_profile=PROFILE,
        conversation_history=[ConversationTurn(role="interviewer", content="Discuss illegal activity.", turn=1)],
        session_metadata=SessionMetadata(),
    )
    try:
        await AgentPipeline(client=llm, bank=FallbackBank()).run(bad)
        raise AssertionError("guardrail should have raised")
    except PipelineError as exc:
        print("7. Guardrail pre-flight OK:", exc)

    print("\nF9 pipeline smoke tests passed.")


if __name__ == "__main__":
    asyncio.run(main())