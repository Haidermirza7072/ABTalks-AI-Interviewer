"""Smoke test for F5 context assembly + windowing."""
from agent.context import (
    assert_guardrails,
    assemble_context,
    build_curriculum_context,
    guardrail_check,
    window_history,
)
from agent.schemas import (
    EvidenceEntry,
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    SessionMetadata,
)

# 1. Windowing
turns = [
    ConversationTurn(
        role="interviewer" if i % 2 == 1 else "candidate",
        content=f"Q{i}" if i % 2 == 1 else f"A{i}",
        turn=i,
    )
    for i in range(1, 9)
]
short_turns = turns[:4]
w1, s1 = window_history(short_turns)
assert len(w1) == 4 and not s1, "short history must be untouched"

w2, s2 = window_history(turns, summary="candidate was good on RAG")
assert len(w2) == 5, f"expected summary + 4 recent, got {len(w2)}"
assert s2 and w2[0].content.startswith("[Summary of earlier turns]")

w3, s3 = window_history(turns, None)
assert len(w3) == 4 and not s3
print("1. Windowing OK: 8 ->", len(w2), "with summary; ->", len(w3), "without")

# 2. Curriculum context
ctx = build_curriculum_context(["day_12", "day_13", "day_99"])
assert "day_12 (Introduction to RAG" in ctx
assert "day_99" not in ctx
assert "day_13" in ctx
print("2. Curriculum context OK")

# 3. Guardrail pre-check
assert guardrail_check("normal text") == []
hits = guardrail_check("never discuss weapons or illegal activity")
assert sorted(hits) == ["illegal activity", "weapons"]
dedup = assert_guardrails("weapons", "weapons again")
assert dedup == ["weapons"]
print("3. Guardrail pre-check OK:", hits)

# 4. Full question assembly
profile = CandidateProfile(
    candidate_id="cand_001_anxious_alex",
    completed_missions=["day_01", "day_12", "day_13"],
    skipped_topics=["day_14"],
    tools_used=["ChromaDB", "LangChain"],
)
request = AgentRequest(
    task="generate_question",
    candidate_profile=profile,
    conversation_history=turns[:4],
    session_metadata=SessionMetadata(
        turn_count=4,
        covered_days=["day_12"],
        current_persona="senior_engineer",
        question_types_used=["challenge"],
    ),
    evidence_log=[
        EvidenceEntry(topic="RAG", signal="strong", evidence="Explained retrieval")
    ],
)
ctx = assemble_context(request)
assert len(ctx.messages) == 2 and ctx.messages[0]["role"] == "system"
assert "SENIOR ENGINEER" in ctx.system_prompt
assert "cand_001_anxious_alex" in ctx.user_prompt
assert "day_12" in ctx.user_prompt or "day_12" in ctx.curriculum_context
assert ctx.uncovered_days[0] == "day_01"
assert ctx.current_persona == "senior_engineer"
print("4. Question assembly OK: system", len(ctx.system_prompt), "user", len(ctx.user_prompt))

# 5. Override persona
ctx_b = assemble_context(request, overwrite_persona="staff_engineer")
assert "STAFF ENGINEER" in ctx_b.system_prompt
print("5. Persona override OK")

# 6. Follow-up assembly uses last answer
request_f = AgentRequest(
    task="generate_followup",
    candidate_profile=profile,
    conversation_history=[
        ConversationTurn(role="interviewer", content="Tell me about RAG.", turn=1),
        ConversationTurn(
            role="candidate", content="ChromaDB embedding similarity.", turn=2
        ),
    ],
    session_metadata=SessionMetadata(turn_count=6, question_types_used=["challenge"]),
    evidence_log=[
        EvidenceEntry(topic="RAG", signal="strong", evidence="Explained retrieval")
    ],
)
ctxf = assemble_context(request_f)
assert "ChromaDB" in ctxf.user_prompt  # last answer injected
assert "references_claim" in ctxf.user_prompt
print("6. Follow-up assembly OK")

# 7. Feedback task
fb3 = AgentRequest(
    task="synthesize_feedback",
    candidate_profile=profile,
    conversation_history=turns[:6],
    session_metadata=SessionMetadata(turn_count=12),
    evidence_log=[EvidenceEntry(topic="RAG", signal="strong", evidence="Explained")],
)
ctxg = assemble_context(fb3)
assert '"readiness_score"' in ctxg.user_prompt
print("7. Feedback assembly OK")

print("\nF5 context assembly smoke tests passed.")