"""PoC 2 — full interview loop, fully offline (no API key).

Demonstrates a candidate progressing through questions and a final
feedback report, using the offline fallback bank as the "model".
Always works — no network, no credentials.  Swap in an
OPENROUTER_API_KEY to get real LLM answers instead.
Run:  docker compose run --rm agent python scripts/poc/poc2_offline_interview.py
"""
import asyncio

from agent.config import settings
from agent.pipeline import run_agent, update_session_after_run
from agent.schemas import (
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    SessionMetadata,
)


async def main() -> None:
    mode = "REAL LLM" if settings.openrouter_api_key else "OFFLINE FALLBACK BANK"
    print(f"== Thread Puller — offline interview loop (mode: {mode}) ==\n")

    session = SessionMetadata(session_id="poc2_offline")
    profile = CandidateProfile(
        candidate_id="cand_poc2",
        completed_missions=[f"day_{i:02d}" for i in range(1, 26)],
        skipped_topics=["day_06", "day_07"],
        tools_used=["Python", "FastAPI", "ChromaDB"],
    )
    history: list[ConversationTurn] = []

    for turn in range(1, 5):
        request = AgentRequest(
            task="generate_question",
            candidate_profile=profile,
            conversation_history=history,
            session_metadata=session,
        )
        out = await run_agent(request)
        q = out.output.question
        print(f"[Q{turn}] {q}")
        print(f"        type={out.output.question_type.value} | "
              f"day={out.output.target_day} | fallback={out.fallback_used}")
        history.append(
            ConversationTurn(role="candidate", content=f"Generic answer {turn}.", turn=turn)
        )
        update_session_after_run(request, out)

    fb = await run_agent(
        AgentRequest(
            task="synthesize_feedback",
            candidate_profile=profile,
            conversation_history=history,
            session_metadata=session,
        )
    )
    print("\n== FEEDBACK REPORT ==")
    print(f"readiness_score : {fb.output.readiness_score}")
    print(f"overall_summary : {fb.output.overall_summary or '(partial template)'}")


if __name__ == "__main__":
    asyncio.run(main())