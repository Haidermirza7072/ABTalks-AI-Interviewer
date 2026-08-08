"""Smoke test for F3 taxonomy + diversity queue."""
from agent.schemas import QuestionType
from agent.taxonomy import QuestionTypeQueue, type_guide_text

q = QuestionTypeQueue()

# 1. Fresh queue: all types allowed
for t in QuestionType:
    assert q.is_allowed(t), f"{t} should be allowed initially"
print("1. All types allowed on fresh queue")

# 2. Record challenge, expand; challenge must NOT be allowed (within 2 turns)
q.record(QuestionType.CHALLENGE)
q.record(QuestionType.EXPAND)
assert not q.is_allowed(QuestionType.CHALLENGE), "challenge repeated within 2 turns"
assert not q.is_allowed(QuestionType.EXPAND), "expand repeated within 2 turns"
assert q.is_allowed(QuestionType.COMPARE)
print("2. Diversity rule enforced: challenge/expand blocked in next 2 turns")

# 3. After 3 different types, first type becomes allowed again
q.record(QuestionType.COMPARE)  # recent = [challenge, expand, compare]
assert q.is_allowed(QuestionType.CHALLENGE), "challenge should be allowed after 2 turns"
print("3. Sliding window works")

# 4. Autowraps strings and caps window at 3
q2 = QuestionTypeQueue(["challenge", "expand", "compare", "challenge"])
assert len(q2.recent) == 3, f"window must cap at 3, got {len(q2.recent)}"
print("4. Window caps at 3:", [t.value for t in q2.recent])

# 5. Distinct count + diversity target
q3 = QuestionTypeQueue(["challenge", "expand", "compare", "apply", "teach", "meta"])
assert q3.distinct_count() == 6
assert q3.diversity_satisfied()
print("5. distinct_count=6, diversity satisfied")

# 6. type_guide_text renders
guide = type_guide_text()
assert "challenge: push back" in guide
assert "meta:" in guide
print("6. type_guide_text OK")

print("\nF3 taxonomy smoke tests passed.")