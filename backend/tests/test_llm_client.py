import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.llm_client import check_llm_health
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
async def test_check_llm_health_failure():
    """Test health check returns False on non-200 response."""
    mock_res = MagicMock()
    mock_res.status_code = 500

    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            result = await check_llm_health()
            assert result is False

@pytest.mark.asyncio
async def test_check_llm_health_exception():
    """Test health check returns False on network exception."""
    with patch.object(settings, "OPENROUTER_API_KEY", "mock_key"):
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
            result = await check_llm_health()
            assert result is False
