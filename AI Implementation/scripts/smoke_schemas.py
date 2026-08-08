"""Quick smoke test for agent.schemas — run inside Docker."""
import json
import sys

from agent.schemas import (
    AgentRequest,
    AgentOutput,
    FeedbackReport,
    QuestionType,
    Persona,
    template_feedback_failure,
)

# 1. Parse a full AgentRequest from Section J example JSON
raw = {
    "task": "generate_question",
    "candidate_profile": {
        "candidate_id": "c1",
        "completed_missions": ["day_12"],
        "skipped_topics": ["day_14"],
        "tools_used": ["ChromaDB"],
    },
    "conversation_history": [
        {"role": "interviewer", "content": "Hello", "turn": 1},
        {"role": "candidate", "content": "Hi", "turn": 2},
    ],
    "session_metadata": {
        "turn_count": 2,
        "covered_days": ["day_12"],
        "current_persona": "senior_engineer",
        "question_types_used": ["challenge"],
    },
    "evidence_log": [
        {"topic": "RAG", "signal": "strong", "evidence": "Explained retrieval pipeline"}
    ],
}
req = AgentRequest.model_validate(raw)
print("1. Request OK:", req.task.value, "|", req.candidate_profile.candidate_id)

# 2. Build an AgentOutput (Section J output schema)
out = AgentOutput(
    task="generate_question",
    output={
        "question": "Why ChromaDB?",
        "target_day": "day_12",
        "question_type": "challenge",
        "persona": "senior_engineer",
        "confidence": 0.92,
        "validation_passed": True,
    },
    fallback_used=False,
    latency_ms=1200,
)
print("2. Output OK:", out.output.question, "|", out.output.question_type.value)

# 3. Template feedback fallback (Section G)
fb = template_feedback_failure(["day_12", "day_14"])
print("3. Template FB:", fb.is_partial, "|", (fb.disclaimer or "")[:50])

# 4. Extra-field rejection (extra="forbid")
try:
    AgentRequest(task="generate_question", candidate_profile={"candidate_id": "c1"}, bogus=True)
    print("4. FAIL: extra field was accepted")
    sys.exit(1)
except Exception as e:
    print("4. Extra-forbid OK:", type(e).__name__)

# 5. Round-trip serialization
rt = AgentOutput.model_validate_json(out.model_dump_json())
print("5. Round-trip OK:", rt.output.question == "Why ChromaDB?")

# 6. Enum values
print("6. QuestionType values:", [t.value for t in QuestionType])
print("   Persona values:", [p.value for p in Persona])

print("\nAll schema smoke tests passed.")
