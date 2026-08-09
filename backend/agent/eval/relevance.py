"""Semantic relevance: embed question vs curriculum objectives (Section E).

Uses the OpenRouter embeddings endpoint (Feature 6) to compute cosine
similarity between a generated question and the target day's learning
objectives.  Target: relevance >= 85% of questions score > 0.65.
"""
from __future__ import annotations

from agent.llm_client import LLMClient, cosine_similarity


async def relevance_score(
    client: LLMClient,
    question: str,
    learning_objectives: list[str],
) -> float | None:
    """Cosine similarity between *question* and the day's objectives.

    Returns None when embedding fails (caller treats as unknown).
    """
    if not learning_objectives:
        return None
    try:
        vectors = await client.embed([question, " ".join(learning_objectives)])
    except Exception:
        return None
    return cosine_similarity(vectors[0], vectors[1])


async def relevance_passed(
    client: LLMClient,
    question: str,
    learning_objectives: list[str],
    threshold: float | None = None,
) -> bool:
    """True when the question is semantically close to the objectives."""
    threshold = threshold if threshold is not None else _threshold()
    score = await relevance_score(client, question, learning_objectives)
    if score is None:
        return True  # unknown embedding failure -> don't hard-fail here
    return score >= threshold


def _threshold() -> float:
    from agent.config import settings

    return settings.relevance_threshold