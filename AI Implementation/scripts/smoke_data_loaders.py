"""Smoke test for F2 data loaders."""
from agent.data import (
    get_day,
    get_uncovered_days,
    is_valid_day,
    list_all_day_ids,
    load_all_candidates,
    load_candidate,
    load_curriculum,
)

# 1. Curriculum loads 31 days
print("1. Curriculum days:", len(load_curriculum()))
assert len(load_curriculum()) == 31, "expected 31 days"
assert list_all_day_ids() == sorted(list_all_day_ids())
assert is_valid_day("day_14")
assert not is_valid_day("day_99")

# 2. Day lookup with metadata
day = get_day("day_12")
print("2. day_12:", day.title, "| tools:", day.tools)
assert "RAG" in day.title

# 3. Candidates load
print("3. Candidates:", len(load_all_candidates()))
assert len(load_all_candidates()) == 5

# 4. Alex profile with skipped topics
alex = load_candidate("cand_001_anxious_alex")
print("4. Alex skipped:", alex.skipped_topics)
assert alex.skipped_topics == ["day_14"]

# 5. Uncovered: completed-but-uncovered first, covered excluded
uncovered = get_uncovered_days(alex, covered_days=["day_12"])
print("5. Alex uncovered (completed-first):", uncovered[:5])
assert uncovered[0] == "day_01"
assert "day_12" not in uncovered
assert "day_14" in uncovered  # skipped days come after completed ones

# 6. Priority ordering: skipped days appear right after completed days
gaps = load_candidate("cand_003_leo_gaps")
uncovered_gaps = get_uncovered_days(gaps)
print("6. Leo uncovered:", uncovered_gaps[:21])
# Leo completed day_01..day_17, skipped day_18..day_21
assert uncovered_gaps[16] == "day_17"
assert uncovered_gaps[17] == "day_18", "skipped days must follow completed days"
assert uncovered_gaps[21] == "day_22", "unknown days come last"

print("\nF2 loader smoke tests passed.")