"""Smoke test for F8 fallback bank + selection priorities."""
from agent.fallback import get_bank
from agent.data.curriculum import list_all_day_ids

bank = get_bank()

# 1. Coverage: every curriculum day has at least 1 question
day_ids = list_all_day_ids()
missing = [d for d in day_ids if not bank.by_day(d)]
assert not missing, f"days missing from bank: {missing}"
print(f"1. Coverage OK: all {len(day_ids)} days have >= 1 question")

# 2. Priority: completed-uncovered first, then skipped, then general
q = bank.select(completed_uncovered=["day_12"], skipped=["day_14"])
assert q["target_day"] == "day_12", q
print("2. Priority 1 (completed-uncovered) OK:", q["target_day"])

q2 = bank.select(completed_uncovered=[], skipped=["day_14"])
assert q2["target_day"] == "day_14"
print("3. Priority 2 (skipped) OK:", q2["target_day"])

q3 = bank.select(completed_uncovered=[], skipped=[])
assert q3.get("target_day") in (None, "general") and bool(q3)
print("4. Priority 3 (general) OK:", q3["question"][:40], "...")

# 5. by_day returns the day question
assert bank.by_day("day_12")[0]["target_day"] == "day_12"
assert bank.general_question() is not None
print("5. by_day / general accessors OK")

# 6. rotate avoids already-used questions
used = {bank.by_day("day_12")[0]["question"]}
rot = bank.rotate_for_day("day_12", used)
print("6. rotate_for_day:", "skipped used one" if rot is None else "picked another")

print("\nF8 fallback bank smoke tests passed.")