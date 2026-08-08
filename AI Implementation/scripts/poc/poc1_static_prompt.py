"""PoC 1 — static prompt gallery (no API key needed).

Renders what the LLM would actually see for each of the four tasks,
proving prompt quality without spending a single token.
Run:  docker compose run --rm agent python scripts/poc/poc1_static_prompt.py
"""
import asyncio

from agent.context import assemble_context
from agent.schemas import AgentRequest, CandidateProfile, SessionMetadata
from tests.fixtures.conftest_helpers import transcript  # noqa: F401  (demo ctx)


def build_request() -> AgentRequest:
    return AgentRequest(
        task="generate_question",
        candidate_profile=CandidateProfile(
            candidate_id="cand_demo",
            completed_missions=["day_01", "day_02", "day_03", "day_04", "day_05"],
            skipped_topics=["day_06"],
            tools_used=["Python", "ChromaDB"],
        ),
        conversation_history=[
            {"role": "candidate", "content": "I built a RAG pipeline.", "turn": 1},
            {"role": "candidate", "content": "Chunking with 200-token overlap.", "turn": 2},
        ],
        session_metadata=SessionMetadata(session_id="poc_static"),
    )


async def main() -> None:
    req = build_request()
    for task in ("generate_question", "generate_followup", "summarize"):
        req.task = task
        ctx = assemble_context(req)
        print("=" * 78)
        print(f"TASK: {task}  ({len(ctx.system_prompt)} sys / {len(ctx.user_prompt)} user chars)")
        print("=" * 78)
        for msg in ctx.messages:
            print(f"---- {msg['role']} ----")
            print(msg["content"][:1200])
            print()
        print()


if __name__ == "__main__":
    asyncio.run(main())