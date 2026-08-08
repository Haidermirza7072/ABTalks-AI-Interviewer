"""Probe candidate model IDs against OpenRouter until one responds."""
import asyncio

from agent.config import settings
from agent.llm_client import LLMClient, LLMUnavailableError

CANDIDATES = [
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-24b-instruct",
    "qwen/qwen-2.5-72b-instruct",
]


async def main() -> None:
    client = LLMClient()
    for model in CANDIDATES:
        try:
            raw = await client.chat(
                [{"role": "user", "content": "Reply with the single word: ok"}],
                settings.question_config,
                model=model,
            )
            print(f"WORKING: {model} -> {raw[:60]!r}")
            break
        except LLMUnavailableError as exc:
            print(f"DEAD   : {model} -> {str(exc)[:80]}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR  : {model} -> {type(exc).__name__}: {str(exc)[:80]}")


if __name__ == "__main__":
    asyncio.run(main())