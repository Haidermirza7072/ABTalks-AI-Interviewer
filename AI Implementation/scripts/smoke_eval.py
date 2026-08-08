"""Smoke test for F13 evaluation metrics (offline)."""
import json

from agent.eval.metrics import (
    bias_audit,
    evaluate_logs,
    pearson_r,
)

records = [
    {"session_id": "s1", "candidate_id": "c1", "task": "generate_question",
     "actual_type": "challenge", "relevance_score": 0.8,
     "validation_passed": True, "persona": "senior_engineer"},
    {"session_id": "s1", "candidate_id": "c1", "task": "generate_followup",
     "actual_type": "expand", "references_claim": "ChromaDB",
     "validation_passed": True, "persona": "hiring_manager"},
    {"session_id": "s1", "candidate_id": "c1", "task": "synthesize_feedback",
     "validation_passed": True, "persona": "staff_engineer"},
]

report = evaluate_logs(records)
print(json.dumps(report, indent=2, ensure_ascii=False))

assert report["question_relevance"] == 1.0
assert report["schema_compliance"] == 1.0
assert report["type_diversity_avg"] == 2.0
assert report["persona_dominance_violated"] is False

# Pearson sanity
assert abs(pearson_r([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9
assert abs(pearson_r([1, 2, 3], [6, 4, 2]) + 1.0) < 1e-9

# Bias audit: normalize outcome, no skipped-score correlation
r = bias_audit({"a": 1, "b": 10, "c": 2}, {"a": 8.0, "b": 8.0, "c": 8.0})
assert abs(r) < 0.5, f"correlated unexpectedly: {r}"
print(f"Bias audit r={r:.3f} (within cap)")

print("\nF13 metrics smoke tests passed.")