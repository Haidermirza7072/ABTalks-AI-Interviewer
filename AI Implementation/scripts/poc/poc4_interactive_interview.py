"""PoC 4 — interactive interview: you answer, the agent scores each answer,
probes with follow-ups when you're strong, and ends with a feedback report.

Run:  docker compose run --rm agent scripts/poc/poc4_interactive_interview.py
       (docker compose run --rm -it agent ... to keep stdin interactive)
"""
import argparse
import asyncio

from agent.config import settings
from agent.pipeline import run_agent, update_session_after_run
from agent.schemas import (
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    SessionMetadata,
)
from agent.taxonomy import should_generate_followup


def ask(prompt: str) -> str:
    """Blocking input() wrapper (run in a thread for asyncio compat)."""
    return input(prompt)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=int, default=5, help="max turns")
    parser.add_argument("--no-followup", action="store_true",
                        help="never generate follow-ups")
    args = parser.parse_args()

    mode = "REAL LLM" if settings.openrouter_api_key else "OFFLINE FALLBACK BANK"
    print(f"== Thread Puller — interactive interview (mode: {mode}) ==")
    print("Type 'exit' to end early; answer each question as yourself.\n")

    session = SessionMetadata(session_id="poc4_interactive")
    profile = CandidateProfile(
        candidate_id="cand_interactive",
        completed_missions=[f"day_{i:02d}" for i in range(1, 32)],
        skipped_topics=[],
        tools_used=["Python", "FastAPI", "ChromaDB"],
    )
    history: list[ConversationTurn] = []
    last_score: float | None = None

    for turn in range(1, args.questions + 1):
        # 1) ask a fresh question
        req = AgentRequest(
            task="generate_question",
            candidate_profile=profile,
            conversation_history=history,
            session_metadata=session,
        )
        out = await run_agent(req)
        update_session_after_run(req, out)
        q = out.output.question
        print(f"[Q{turn}] {q}")
        print(f"        (type={out.output.question_type.value} | "
              f"day={out.output.target_day}{' | fallback bank' if out.fallback_used else ''})")

        # 2) candidate answers
        answer = await asyncio.to_thread(parse_prompt, "You> ")
        if answer.strip().lower() in ("exit", "quit", "q"):
            break
        history.append(
            ConversationTurn(role="candidate", content=answer.strip(), turn=turn)
        )
        session.turn_count += 1

        # 3) score the answer
        score_req = AgentRequest(
            task="score_answer",
            candidate_profile=profile,
            conversation_history=history,
            session_metadata=session,
        )
        scored = await run_agent(score_req)
        a = scored.output
        last_score = a.score
        print(f"Score: {a.score:.1f}/10")
        if a.strengths:
            print("  strengths:", " | ".join(a.strengths))
        if a.gaps:
            print("  gaps    :", " | ".join(a.gaps))

        # 4) follow-up? (high score or many skipped days)
        skip_ratio = len(profile.skipped_topics) / max(len(profile.completed_missions), 1)
        if (
            not args.no_followup
            and should_generate_followup(
                latest_score=a.score,
                validation_passed=scored.validation_passed,
                skip_ratio=skip_ratio,
            )
        ):
            fu_req = AgentRequest(
                task="generate_followup",
                candidate_profile=profile,
                conversation_history=history,
                session_metadata=session,
            )
            fu = await run_agent(fu_req)
            update_session_after_run(fu_req, fu)
            print(f"[Follow-up] {fu.output.question}\n")
            fu_answer = await asyncio.to_thread(parse_prompt, "Answer> ")
            if fu_answer.strip().lower() in ("exit", "quit", "q"):
                break
            history.append(
                ConversationTurn(role="candidate", content=fu_answer.strip(), turn=turn + 1)
            )
            session.turn_count += 1
        else:
            print()

    # 5) end-of-interview feedback report
    print("\n== END OF INTERVIEW — synthesizing feedback ==")
    fb_req = AgentRequest(
        task="synthesize_feedback",
        candidate_profile=profile,
        conversation_history=history,
        session_metadata=session,
    )
    fb = await run_agent(fb_req)
    r = fb.output
    print(f"\nReadiness score: {r.readiness_score}/10")
    if r.strengths:
        print("\nStrengths:")
        for s in r.strengths:
            print(f"  - {s.claim}  (\"{s.citation[:60]}\")" if s.citation else f"  - {s.claim}")
    if r.growth_areas:
        print("Growth areas:")
        for g in r.growth_areas:
            print(f"  - {g.claim}")
    if r.overall_summary:
        print(f"\nSummary: {r.overall_summary}")
    if r.is_partial:
        print("\n(partial template — transcript was too thin for full evaluation)")


def parse_prompt(label: str) -> str:
    return input(label)


if __name__ == "__main__":
    asyncio.run(main())