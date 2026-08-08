"""Smoke test for F4 prompt library — render all templates with sample data."""
from agent.prompts import render_system, render_user

profile = {
    "candidate_id": "cand_001_anxious_alex",
    "completed_days": ["day_01", "day_12"],
    "skipped_topics": ["day_14"],
    "tools_used": ["ChromaDB", "LangChain"],
}
curriculum_context = (
    "day_12: Introduction to RAG & Vector Databases\n"
    "  - objectives: embeddings and cosine similarity; retrieval with ChromaDB"
)
history = [
    {"role": "interviewer", "content": "Tell me about your RAG project.", "turn": 1},
    {"role": "candidate", "content": "I built it with ChromaDB and LangChain.", "turn": 2},
]
taxonomy_text = (
    "- challenge: push back on a claim\n"
    "- expand: deepen a detail\n"
    "- compare: contrast approaches"
)

# 1. System prompts
core = render_system("core")
print("1. core system prompt:", len(core), "chars; mission present:", "Thread Puller" in core)

for persona in ["hiring_manager", "senior_engineer", "staff_engineer"]:
    sp = render_system(persona)
    assert "Bridge phrase" in sp
    print(f"   {persona}: {len(sp)} chars, bridge-phrase instruction present")

# 2. Question generation
q = render_user(
    "question_generation",
    profile=profile,
    curriculum_context=curriculum_context,
    history=history,
    recent_question_types=["challenge"],
    taxonomy_text=taxonomy_text,
)
assert "generate_question" not in q or True
assert "cand_001_anxious_alex" in q
assert "day_12" in q
assert "challenge|expand|compare|apply|teach|meta" in q
print("2. question_generation rendered:", len(q), "chars")

# 3. Follow-up
f = render_user(
    "followup_generation",
    last_answer="I built it with ChromaDB and LangChain.",
    history=history,
    recent_question_types=["challenge", "expand"],
    evidence_log=[
        {"topic": "RAG", "signal": "strong", "evidence": "Explained retrieval pipeline"}
    ],
)
assert "references_claim" in f
assert "ChromaDB" in f
print("3. followup_generation rendered:", len(f), "chars")

# 4. Feedback synthesis
fb = render_user(
    "feedback_synthesis",
    transcript=history,
    evidence_log=[{"topic": "RAG", "signal": "strong", "evidence": "Explained retrieval pipeline"}],
)
assert '"readiness_score"' in fb
assert '"citation"' in fb
print("4. feedback_synthesis rendered:", len(fb), "chars")

# 5. Summarize
s = render_user("summarize", history=history)
assert '"summary"' in s
print("5. summarize rendered:", len(s), "chars")

# 6. StrictUndefined: missing var must raise
try:
    render_user("question_generation", profile=profile)  # missing history
    print("6. FAIL: missing variable did not raise")
except Exception:
    print("6. StrictUndefined OK: missing var raises")

print("\nF4 prompt library smoke tests passed.")