"""Typed data loaders — curriculum + candidate profiles (Section C/G2)."""
from agent.data.candidate import (
    day_status,
    get_uncovered_days,
    load_all_candidates,
    load_candidate,
)
from agent.data.curriculum import (
    get_day,
    is_valid_day,
    list_all_day_ids,
    load_curriculum,
)

__all__ = [
    "day_status",
    "get_day",
    "get_uncovered_days",
    "is_valid_day",
    "list_all_day_ids",
    "load_all_candidates",
    "load_candidate",
    "load_curriculum",
]