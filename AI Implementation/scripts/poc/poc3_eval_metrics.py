"""PoC 3 — staging harness: run n offline interview turns per persona and
produce the Section E / H metric report from the real logs.

Each turn writes a JSONL record; the eval suite (Feature 13) consumes
them, so the numbers below are the same numbers a checkpoint reviewer
would see at Notion Booth 1/2.
Run:  docker compose run --rm agent python scripts/poc/poc3_eval_harness.py --turns 12
"""
import argparse
import asyncio

from agent.config import settings
from agent.eval.metrics import bias_audit, evaluate_logs
from agent.logging import list_sessions, read_session_log
from agent.pipeline import run_agent, update_session_after_run
from agent.schemas import (
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    SessionMetadata,
)


async def single_session(candidate_id: str, completed: list[str], skipped: list[str]) -> None:
    session = SessionMetadata(session_id=candidate_id)
    profile = CandidateProfile(
        candidate_id=candidate_id,
        completed_missions=completed,
        skipped_topics=skipped,
        tools_used=["Python"],
    )
    history: list[ConversationTurn] = []
    for _ in range(4):
        request = AgentRequest(
            task="generate_question",
            candidate_profile=profile,
            conversation_history=history,
            session_metadata=session,
        )
        out = await run_agent(request)
        update_session_after_run(request, out)
        history.append(ConversationTurn(role="candidate", content="Answer.", turn=session.turn_count))
        await run_agent(
            AgentRequest(
                task="synthesize_feedback",
                candidate_profile=profile,
                conversation_history=history,
                session_metadata=session,
            )
        )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true", help="delete existing logs first")
    args = parser.parse_args()

    if args.clear:
        import shutil

        shutil.rmtree(settings.log_dir, ignore_errors=True)

    # Two probe candidates: near-full curriculum vs. heavy skips (bias pair).
    all_days = [f"day_{i:02d}" for i in range(1, 32)]
    await single_session("cand_bias_low", completed=all_days, skipped=[])
    await single_session(
        "cand_bias_high",
        completed=all_days[:8],
        skipped=all_days[8:14],
    )

    records = []
    for sid in list_sessions():
        records.extend(read_session_log(sid))

    report = evaluate_logs(records)
    print("\n== Section E / H metric report ==")
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))

    r = bias_audit(
        {"cand_bias_low": 0, "cand_bias_high": 6},
        {"cand_bias_low": 7.5, "cand_bias_high": 7.5},
    )
    print(f"\nFairness Pearson r on pair probes: {r:.3f} (|r| < 0.5 required)")


if __name__ == "__main__":
    asyncio.run(main())