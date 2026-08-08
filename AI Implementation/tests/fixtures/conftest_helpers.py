"""Shared pytest fixtures (Section L testing strategy).

Provides mock LLM clients, base candidate profiles, transcripts, and
session metadata used across unit / integration / edge-case / bias tests.
"""
from __future__ import annotations

import pytest

from agent.schemas import (
    ConversationTurn,
    EvidenceEntry,
    AgentRequest,
    CandidateProfile,
    SessionMetadata,
)


@pytest.fixture
def profile_alex() -> CandidateProfile:
    """Candidate with a couple of skipped days (middle of the pack)."""
    return CandidateProfile(
        candidate_id="cand_001_anxious_alex",
        completed_missions=[
            "day_01", "day_02", "day_03", "day_04", "day_05", "day_06", "day_07",
            "day_08", "day_09", "day_10", "day_11", "day_12", "day_13",
            "day_15", "day_16", "day_17", "day_18", "day_19", "day_20", "day_21",
            "day_22", "day_23", "day_24", "day_25", "day_26", "day_27", "day_28",
            "day_29", "day_30", "day_31",
        ],
        skipped_topics=["day_14"],
        tools_used=["Python", "ChromaDB", "LangChain", "FastAPI"],
    )


@pytest.fixture
def profile_leapless() -> CandidateProfile:
    """Candidate who completed everything (bias probe low)."""
    from agent.data.curriculum import list_all_day_ids

    return CandidateProfile(
        candidate_id="cand_005_bias_probe_low",
        completed_missions=list_all_day_ids(),
        skipped_topics=[],
        tools_used=["Python"],
    )


@pytest.fixture
def profile_heavy_skips() -> CandidateProfile:
    """Candidate with many skipped days (bias probe high)."""
    return CandidateProfile(
        candidate_id="cand_004_bias_probe_high",
        completed_missions=["day_01", "day_02", "day_03"],
        skipped_topics=["day_04", "day_05", "day_06", "day_07", "day_08"],
        tools_used=["Python"],
    )


@pytest.fixture
def transcript() -> list[ConversationTurn]:
    return [
        ConversationTurn(role="interviewer", content="Tell me about your RAG project.", turn=1),
        ConversationTurn(role="candidate", content="I built it with ChromaDB and LangChain.", turn=2),
        ConversationTurn(role="interviewer", content="How did you chunk the documents?", turn=3),
        ConversationTurn(role="candidate", content="By sections with 200-token overlap.", turn=4),
    ]


@pytest.fixture
def evidence() -> list[EvidenceEntry]:
    return [EvidenceEntry(topic="RAG", signal="strong", evidence="Explained retrieval")]


def make_request(
    task: str,
    profile: CandidateProfile,
    history: list[ConversationTurn] | None = None,
    session: SessionMetadata | None = None,
) -> AgentRequest:
    """Helper to build a valid request quickly."""
    return AgentRequest(
        task=task,  # type: ignore[arg-type]
        candidate_profile=profile,
        conversation_history=history or [],
        session_metadata=session or SessionMetadata(),
        evidence_log=[EvidenceEntry(topic="RAG", signal="strong", evidence="x")],
    )