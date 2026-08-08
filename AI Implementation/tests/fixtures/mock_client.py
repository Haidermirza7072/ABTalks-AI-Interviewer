"""Standalone deterministic mocks for the real LLM client (no pytest needed).

FakeLLM returns canned JSON payloads per task so that pipeline tests are
fully deterministic and network-free (Section L unit + integration).
The contract mirrors the real ``LLMClient.chat_json``: returns a parsed
``dict | None`` (None when parsing fails), and stores raw payloads.
"""
from __future__ import annotations

import json

VALID_QUESTION_JSON = """{
  "question": "Why ChromaDB and cosine similarity for vector retrieval instead of a full scan?",
  "target_day": "day_12",
  "question_type": "challenge"
}"""

VALID_FOLLOWUP_JSON = """{
    "question": "Which part of ChromaDB worried you most at scale?",
    "target_day": "day_07",
    "question_type": "expand"
}"""

VALID_FEEDBACK_JSON = """{
    "readiness_score": 7.5,
    "strengths": [
        {"claim": "Strong retrieval explanation", "citation": "I built it with ChromaDB and LangChain."}
    ],
    "growth_areas": [
        {"claim": "Deeper on vector search math", "citation": "By sections with 200-token overlap."}
    ],
    "overall_summary": "Solid foundation on RAG, deepen the math."
}"""

VALID_SUMMARY_JSON = """{
    "summary": "Candidate built a RAG system with ChromaDB; strengths in retrieval, needs depth on trade-offs."
}"""


def _parsed(payload: str) -> dict | None:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


class FakeLLM:
    """Chat client returning canned JSON.  Records the last planner payload."""

    def __init__(self, *, question: str | None = None, followup: str | None = None):
        self.question_reply = question or VALID_QUESTION_JSON
        self.followup_reply = followup or VALID_FOLLOWUP_JSON
        self.calls: list[dict] = []

    async def chat_json(self, messages, config=None):
        last_prompt = messages[-1]["content"]
        self.calls.append({"config": config, "last_prompt": last_prompt})
        if "follow-up question" in last_prompt:
            return _parsed(self.followup_reply)
        if "Synthesize" in last_prompt or "feedback report" in last_prompt:
            return _parsed(VALID_FEEDBACK_JSON)
        if "Summarize" in last_prompt or "summary" in last_prompt:
            return _parsed(VALID_SUMMARY_JSON)
        return _parsed(self.question_reply)

    async def embed(self, texts):
        """Deterministic pseudo-embeddings: identical texts get identical vectors."""
        if isinstance(texts, str):
            texts = [texts]
        return [
            [sum(ord(c) for c in t) % 101 / 101.0, len(t) % 97 / 100.0]
            for t in texts
        ]