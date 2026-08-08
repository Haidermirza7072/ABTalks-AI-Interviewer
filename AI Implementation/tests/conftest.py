"""pytest configuration + shared fixtures (Section L)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.schemas import AgentRequest, EvidenceEntry, SessionMetadata  # noqa: E402
from tests.fixtures.conftest_helpers import (  # noqa: E402
    evidence,
    profile_alex,
    profile_heavy_skips,
    profile_leapless,
    transcript,
)


@pytest.fixture
def make_request():
    """Factory fixture building a minimal valid AgentRequest."""

    def _make(task, profile, history=None, session=None, evidence_log=None):
        return AgentRequest(
            task=task,
            candidate_profile=profile,
            conversation_history=history or [],
            session_metadata=session or SessionMetadata(),
            evidence_log=evidence_log or [
                EvidenceEntry(topic="RAG", signal="strong", evidence="x")
            ],
        )

    return _make


def pytest_collection_modifyitems(items):
    """Defer live (network) tests to the end."""
    for item in items:
        if "live" in item.keywords:
            item.add_marker(pytest.mark.slow)