import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.models.schemas import InterviewSession, FeedbackReport
from app.services.llm_client import (
    check_llm_health,
    generate_next_question,
    generate_feedback_report,
    get_fallback_question,
)
from app.config import settings

@pytest.mark.asyncio
async def test_check_llm_health_no_key():
    """Test health check returns False when API key is missing."""
    with patch.object(settings, "OPENROUTER_API_KEY", ""):
        result = await check_llm_health()
        assert result is False

@pytest.mark.asyncio
async def test_check_llm_health_success():
    """Test health check returns True on 200 response."""
    mock_res = MagicMock()
    mock_res.status_code = 200

    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            result = await check_llm_health()
            assert result is True

@pytest.mark.asyncio
async def test_generate_next_question_llm_success():
    """Test LLM question generation when OpenRouter succeeds."""
    session = InterviewSession(candidate_id="cand_101")
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "choices": [{"message": {"content": "What is FastAPI dependency injection?"}}]
    }

    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            question = await generate_next_question(session, None, "I love Python.")
            assert question == "What is FastAPI dependency injection?"
            assert len(session.conversation_history) == 2

@pytest.mark.asyncio
async def test_generate_next_question_timeout_fallback():
    """Test falling back to fallback question on LLM timeout."""
    session = InterviewSession(candidate_id="cand_101")
    
    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
            question = await generate_next_question(session, None, "Some answer")
            assert isinstance(question, str)
            assert len(question) > 0

@pytest.mark.asyncio
async def test_generate_feedback_report_fallback():
    """Test generating feedback report using fallback synthesis."""
    session = InterviewSession(candidate_id="cand_101")
    session.turn_count = 3
    session.conversation_history = [
        {"role": "interviewer", "content": "Question 1"},
        {"role": "candidate", "content": "Answer 1"},
    ]

    report = await generate_feedback_report(session, is_partial=False)
    assert isinstance(report, FeedbackReport)
    assert report.is_partial is False
    assert report.readiness_score >= 1

@pytest.mark.asyncio
async def test_generate_feedback_report_llm_success():
    """Test generating feedback report via mocked LLM JSON response."""
    session = InterviewSession(candidate_id="cand_101")
    session.turn_count = 3

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"readiness_score": 9, "strengths": [{"title": "FastAPI", "evidence": "good"}], "growth_areas": [{"title": "Caching", "resource": "redis doc"}], "communication_tips": ["clear"], "evidence_citations": ["citation 1"]}'
            }
        }]
    }

    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            report = await generate_feedback_report(session, is_partial=False)
            assert report.readiness_score == 9
            assert report.strengths[0]["title"] == "FastAPI"
