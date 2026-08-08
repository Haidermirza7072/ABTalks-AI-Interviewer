"""Smoke test for F7 validation & guardrails."""
from agent.schemas import TaskType
from agent.validation import schema_validate, content_validate, validate_llm_output

transcript = [
    "Tell me about your RAG project.",
    "I built it with ChromaDB and used cosine similarity for retrieval.",
    "How did you chunk the documents?",
    "I chunked by sections with 200-token overlap.",
]

# 1. Valid question passes
good = {
    "question": "Walk me through why you chose ChromaDB for your RAG project.",
    "target_day": "day_12",
    "question_type": "challenge",
    "persona": "senior_engineer",
}
r = validate_llm_output(TaskType.GENERATE_QUESTION, good, recent_question_types=["expand"])
assert r.passed, r.reasons
print("1. Valid question passes:", r.passed)

# 2. Bad target_day fails
bad_day = dict(good, target_day="day_99")
r = validate_llm_output(TaskType.GENERATE_QUESTION, bad_day)
assert not r.passed and any("day_99" in x for x in r.reasons)
print("2. Invalid target_day fails:", r.reasons[0])

# 3. Repeating question type within 2 turns fails
r = validate_llm_output(
    TaskType.GENERATE_QUESTION, good, recent_question_types=["compare", "challenge"]
)
assert not r.passed and any("repeats within 2 turns" in x for x in r.reasons)
print("3. Type repetition fails:", r.reasons[0])

# 4. Schema-invalid JSON fails
r = validate_llm_output(TaskType.GENERATE_QUESTION, {"question": 42})
assert not r.passed
print("4. Schema-invalid fails:", r.reasons[0][:45])

# 5. Feedback with anchored citations passes
feedback = {
    "readiness_score": 7.5,
    "strengths": [
        {"claim": "Good grasp of retrieval.", "citation": "I built it with ChromaDB and used cosine similarity for retrieval."}
    ],
    "growth_areas": [
        {"claim": "Could go deeper on chunking.", "citation": "I chunked by sections with 200-token overlap."}
    ],
    "overall_summary": "Solid fundamentals.",
    "is_partial": False,
}
r = validate_llm_output(TaskType.SYNTHESIZE_FEEDBACK, feedback, transcript=transcript)
assert r.passed, r.reasons
print("5. Feedback with citations passes")

# 6. Feedback with unanchored citation fails
bad_fb = [f for f in [feedback]][0]
bad_fb["strengths"][0]["citation"] = "I invented this quote."
r = validate_llm_output(TaskType.SYNTHESIZE_FEEDBACK, bad_fb, transcript=transcript)
assert not r.passed and any("not in transcript" in x for x in r.reasons)
print("6. Unanchored citation fails:", r.reasons[0][:50])

# 7. Partial template feedback passes without citations
from agent.schemas import template_feedback_failure

t = template_feedback_failure()
assert t.is_partial
r = validate_llm_output(TaskType.SYNTHESIZE_FEEDBACK, dict(t), transcript=transcript)
assert r.passed, r.reasons
print("7. Partial template passes (no citations required)")

# 8. Summary always passes schema
r = validate_llm_output(TaskType.SUMMARIZE, {"summary": "Candidate strong on RAG."})
assert r.passed
print("8. Summarize passes")

print("\nF7 validation & guardrails smoke tests passed.")