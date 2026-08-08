"""Fallback question bank + selection logic (Section G, Section C).

`fallback_questions.json` — pre-written questions for graceful
degradation when the LLM fails. Every curriculum day has at least one
question; plus a few general cohort overview questions.

Selection priority (Section G):
    1. Candidate's completed-but-uncovered days (strength probing).
    2. Candidate's skipped days (gentle probe, never a "gotcha").
    3. General cohort overview question (lowest priority).
"""
from __future__ import annotations

import json
from pathlib import Path

from agent.config import settings


class FallbackBank:
    """Loads and queries the fallback question bank."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.fallback_bank_path
        self._by_day: dict[str, list[dict]] = {}
        self._general: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Fallback bank not found: {self.path}. Run "
                "scripts/generate_fallback_bank.py to create it."
            )
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        items = raw if isinstance(raw, list) else raw.get("questions", [])
        for item in items:
            day_id = item.get("target_day", "")
            if day_id and day_id not in ("general", "overview"):
                self._by_day.setdefault(day_id, []).append(item)
            else:
                self._general.append(item)

    # ── queries ────────────────────────────────────────────

    def by_day(self, day_id: str) -> list[dict]:
        """All fallback questions for a specific day."""
        return self._by_day.get(day_id, [])

    def any_for_days(self, day_ids: list[str]) -> dict | None:
        """First question from the first day in *day_ids* that has one."""
        for day_id in day_ids:
            items = self._by_day.get(day_id, [])
            if items:
                return items[0]
        return None

    def general_question(self) -> dict | None:
        """First general cohort overview question."""
        return self._general[0] if self._general else None

    def select(
        self,
        *,
        completed_uncovered: list[str] | None = None,
        skipped: list[str] | None = None,
    ) -> dict:
        """Pick a fallback question by Section G priority order."""
        for candidate_days in (completed_uncovered or [], skipped or []):
            hit = self.any_for_days(candidate_days)
            if hit:
                return hit
        general = self.general_question()
        if general:
            return general
        raise RuntimeError("Fallback bank is empty — generate it first.")

    def rotate_for_day(self, day_id: str, used: set[str]) -> dict | None:
        """Next unused fallback question for *day_id*. None when exhausted."""
        for item in self._by_day.get(day_id, []):
            if item["question"] not in used:
                return item
        return None


_SINGLETON: FallbackBank | None = None


def get_bank() -> FallbackBank:
    """Process-wide cached bank instance."""
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = FallbackBank()
    return _SINGLETON