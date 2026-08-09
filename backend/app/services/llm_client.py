"""LLM health check utility.

Question generation and feedback synthesis have been moved to
``app.services.agent_bridge`` which delegates to ``agent.pipeline.run_agent``.
This module retains only the health-check ping used by the background task.
"""
import logging
from typing import Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Global flag for health check status
llm_ready: bool = False


async def check_llm_health() -> bool:
    """Ping OpenRouter API to verify connectivity and update llm_ready flag."""
    global llm_ready
    if not settings.OPENROUTER_API_KEY:
        llm_ready = False
        return False

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            res = await client.post(settings.OPENROUTER_API_URL, headers=headers, json=payload)
            if res.status_code == 200:
                llm_ready = True
                return True
            else:
                logger.warning(f"LLM Health check returned status {res.status_code}")
                llm_ready = False
                return False
    except Exception as e:
        logger.warning(f"LLM Health check failed: {e}")
        llm_ready = False
        return False
