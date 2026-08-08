"""Curriculum loader — ground truth for valid interview content (Section C)."""
from __future__ import annotations

import json
import warnings
from functools import lru_cache
from pathlib import Path

from agent.config import settings
from agent.schemas import CurriculumDay


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_curriculum() -> dict[str, CurriculumDay]:
    """Load curriculum.json and return {day_id: CurriculumDay}.

    Accepts Member 1's source format (``{"days": [{"day": 1, "title": ...,
    "type": "SETUP", "tools": [...], "objectives": [...]}]}``) and maps it
    onto the internal :class:`CurriculumDay` schema.
    """
    raw = _read_json(settings.curriculum_path)
    days: dict[str, CurriculumDay] = {}
    # Accept a top-level list, or {"days": [...]} / {"curriculum": [...]}.
    if isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict):
        entries = raw.get("days", raw.get("curriculum", raw))
    else:
        raise ValueError(f"Unexpected curriculum.json structure: {type(raw)!r}")
    if isinstance(entries, dict):
        # {"day_1": {...}, ...} keyed by day_id (day_id inside may be absent).
        for day_id, payload in entries.items():
            if isinstance(payload, dict):
                days[day_id] = CurriculumDay.model_validate(
                    _normalize_entry(payload, day_id)
                )
        return days
    for payload in entries:
        day = CurriculumDay.model_validate(_normalize_entry(payload))
        days[day.day_id] = day
    if len(days) != 31:
        warnings.warn(
            f"Expected 31 curriculum days, found {len(days)} — "
            f"check {settings.curriculum_path}",
            stacklevel=2,
        )
    return days


def _normalize_entry(payload: dict, day_id: str | None = None) -> dict:
    """Map the Member source format onto the internal schema.

    Source: {"day": 1, "title": ..., "type": "SETUP",
              "tools": [...], "objectives": [...]}
    Internal: {"day_id": "day_01", "title": ..., "topics": [],
               "learning_objectives": [...], "tools": [...]}
    """
    day_key = payload.get("day")
    resolved_id = day_id or payload.get("day_id")
    if resolved_id is None and day_key is not None:
        resolved_id = f"day_{int(day_key):02d}"
    if resolved_id is None:
        raise ValueError(f"curriculum entry missing day identifier: {payload!r}")

    out: dict = {"day_id": resolved_id}
    for src, dst in (("title", "title"), ("objectives", "learning_objectives"),
                     ("topics", "topics"), ("tools", "tools")):
        if src in payload:
            out[dst] = payload[src]
    return out


def get_day(day_id: str) -> CurriculumDay | None:
    """Return the CurriculumDay for *day_id* or None if unknown."""
    return load_curriculum().get(day_id)


def is_valid_day(day_id: str) -> bool:
    """True if *day_id* exists in the curriculum (validation guardrail)."""
    return day_id in load_curriculum()


def list_all_day_ids() -> list[str]:
    """All curriculum day IDs in canonical order."""
    return sorted(load_curriculum().keys())