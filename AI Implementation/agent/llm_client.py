"""Async OpenRouter LLM client (Section D/F, Stage 2).

Wraps the OpenAI-compatible ``client`` package pointed at OpenRouter:

    * ``chat()`` — model call with per-task sampling config + timeout.
    * ``embed()`` — text embeddings (OpenRouter embeddings endpoint).
    * ``LLMUnavailableError`` — raised on timeout / 5xx so the pipeline
      can trigger fallback logic.

Model routing: primary (Nemotron) first, automatic switch to the
fallback model (GPT-4o-mini) on failure via ``chat_with_fallback``.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from openai import AsyncOpenAI

from agent.config import ModelConfig, settings


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM API times out or returns 5xx."""


def _extract_json(raw: str) -> dict[str, Any] | None:
    """Parse raw LLM text to a dict.

    Tries direct json.loads first, then a regex extraction of the first
    ```{...}``` block, then a fenced JSON block (```json ... ```).
    Returns None if all attempts fail (Section F Stage 3).
    """
    text = raw.strip()
    # 1. direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    # 2. fenced json block
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        try:
            parsed = json.loads(fence.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    # 3. first braced block
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            parsed = json.loads(brace.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return None


class LLMClient:
    """Thin async client over OpenRouter."""

    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.cfg.openrouter_api_key:
                raise LLMUnavailableError(
                    "OPENROUTER_API_KEY is not set. Set it in .env or the "
                    "environment before running the agent."
                )
            self._client = AsyncOpenAI(
                api_key=self.cfg.openrouter_api_key,
                base_url=self.cfg.openrouter_base_url,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        model_config: ModelConfig,
        model: str | None = None,
        json_mode: bool = True,
    ) -> str:
        """Call the model, returning the *raw* content text.

        Raises :class:`LLMUnavailableError` on timeout or any 5xx/HTTP error
        so the pipeline can fall back.
        """
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": model or self.cfg.primary_model,
            "messages": messages,
            "temperature": model_config.temperature,
            "top_p": model_config.top_p,
            "max_tokens": model_config.max_tokens,
            "timeout": model_config.timeout_seconds,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = await asyncio.wait_for(
                client.chat.completions.create(**kwargs),
                timeout=model_config.timeout_seconds,
            )
            content = resp.choices[0].message.content or ""
            return content
        except asyncio.TimeoutError as exc:
            raise LLMUnavailableError(f"LLM timeout after {model_config.timeout_seconds}s") from exc
        except Exception as exc:  # openai raises APIStatusError etc.
            raise LLMUnavailableError(f"LLM call failed: {exc}") from exc

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model_config: ModelConfig,
        model: str | None = None,
    ) -> dict[str, Any] | None:
        """Chat + parse JSON. Returns None when parsing fails."""
        raw = await self.chat(messages, model_config, model=model)
        return _extract_json(raw)

    async def chat_with_fallback(
        self,
        messages: list[dict[str, str]],
        model_config: ModelConfig,
    ) -> tuple[str, str]:
        """Call primary model; switch to fallback model on failure.

        Returns (content, model_used).
        """
        try:
            content = await self.chat(messages, model_config, model=self.cfg.primary_model)
            return content, self.cfg.primary_model
        except LLMUnavailableError:
            content = await self.chat(
                messages, model_config, model=self.cfg.fallback_model
            )
            return content, self.cfg.fallback_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (OpenRouter embeddings endpoint)."""
        client = self._get_client()
        try:
            resp = await asyncio.wait_for(
                client.embeddings.create(
                    model=self.cfg.embedding_model,
                    input=texts,
                ),
                timeout=30,
            )
            return [item.embedding for item in resp.data]
        except asyncio.TimeoutError as exc:
            raise LLMUnavailableError("Embedding timeout") from exc
        except Exception as exc:
            raise LLMUnavailableError(f"Embedding failed: {exc}") from exc


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two embedding vectors (no numpy needed)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)