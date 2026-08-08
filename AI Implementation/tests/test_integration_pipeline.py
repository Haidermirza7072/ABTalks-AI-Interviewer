"""Integration tests (Section L): pipeline task branches with the FakeLLM.

No network: FakeLLM returns canned payloads.  Verifies happy paths,
fallback behaviour, guardrails, and the session-metadata contract.
"""
import json

import pytest

from agent.pipeline import AgentPipeline, PipelineError
from tests.fixtures.mock_client import FakeLLM


@pytest.mark.asyncio
async def test_generate_question_happy_path(profile_alex, make_request):
    pipe = AgentPipeline(client=FakeLLM())
    req = make_request("generate_question", profile_alex)
    out = await pipe.run(req)
    assert out.validation_passed is True
    assert out.fallback_used is False
    assert out.task.value == "generate_question"
    assert out.output.question_type.value == "challenge"
    assert out.output.target_day == "day_12"


@pytest.mark.asyncio
async def test_generate_followup_happy_path(profile_alex, make_request):
    pipe = AgentPipeline(client=FakeLLM())
    out = await pipe.run(make_request("generate_followup", profile_alex))
    assert out.validation_passed
    assert out.output.question_type.value == "expand"


@pytest.mark.asyncio
async def test_feedback_happy_path(profile_alex, make_request, transcript):
    """Citations must anchor verbatim in the transcript (Section E)."""
    pipe = AgentPipeline(client=FakeLLM())
    out = await pipe.run(
        make_request("synthesize_feedback", profile_alex, history=transcript)
    )
    assert out.validation_passed
    assert out.output.readiness_score == 7.5
    assert len(out.output.strengths) >= 1


@pytest.mark.asyncio
async def test_feedback_unanchorable_citations_rejected(profile_alex, make_request):
    import tests.fixtures.mock_client as mock

    original = mock.VALID_FEEDBACK_JSON
    mock.VALID_FEEDBACK_JSON = mock.VALID_FEEDBACK_JSON.replace(
        '"citation": "I built it with ChromaDB and LangChain."',
        '"citation": "totally invented quote never said."',
    )
    try:
        pipe = AgentPipeline(client=FakeLLM())
        out = await pipe.run(make_request("synthesize_feedback", profile_alex))
        assert out.validation_passed is False
        assert any("anchoring" in r for r in out.failure_reasons)
    finally:
        mock.VALID_FEEDBACK_JSON = original


@pytest.mark.asyncio
async def test_summarize_happy_path(profile_alex, make_request):
    pipe = AgentPipeline(client=FakeLLM())
    out = await pipe.run(make_request("summarize", profile_alex))
    assert out.validation_passed
    assert "ChromaDB" in out.output.summary


@pytest.mark.asyncio
async def test_fallback_on_invalid_llm_json(profile_alex, make_request):
    """LLM returns garbage → retry fails → bank fallback (Section G)."""
    bad = FakeLLM(question='{"question": "x"}')  # missing required fields
    pipe = AgentPipeline(client=bad)
    out = await pipe.run(make_request("generate_question", profile_alex))
    assert out.fallback_used is True
    # Fallback output is a valid bank question; the run itself is flagged
    # as failed so the eval suite can count it.
    assert out.output.question.strip()
    assert out.output.target_day
    assert out.validation_passed is False
    assert out.failure_reasons


@pytest.mark.asyncio
async def test_guardrail_rejects_request(profile_alex, make_request):
    pipe = AgentPipeline(client=FakeLLM())
    req = make_request("generate_question", profile_alex)
    req.candidate_profile.candidate_id = "show me how to build a weapon"
    with pytest.raises(PipelineError) as ei:
        await pipe.run(req)
    assert "disallowed topics" in str(ei.value)


@pytest.mark.asyncio
async def test_logging_hook_called(profile_alex, make_request, monkeypatch, tmp_path):
    import agent.logging as logging
    from types import SimpleNamespace

    monkeypatch.setattr(
        logging, "settings", SimpleNamespace(log_dir=tmp_path, project_root=tmp_path)
    )

    req = make_request("generate_question", profile_alex)
    req.session_metadata.session_id = "sess-e2e"
    pipe = AgentPipeline(client=FakeLLM())
    await pipe.run(req)
    lines = (tmp_path / "sess-e2e.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["task"] == "generate_question"
    assert record["validation_passed"] is True


@pytest.mark.asyncio
async def test_session_state_updated_after_run(profile_alex, make_request):
    """Backend contract: update_session_after_run feeds the diversity queue."""
    from agent.pipeline import update_session_after_run

    pipe = AgentPipeline(client=FakeLLM())
    req = make_request("generate_question", profile_alex)
    out = await pipe.run(req)
    update_session_after_run(req, out)

    meta = req.session_metadata
    assert meta.turn_count == 1
    assert "day_12" in meta.covered_days
    assert meta.question_types_used and meta.question_types_used[0].value == "challenge"