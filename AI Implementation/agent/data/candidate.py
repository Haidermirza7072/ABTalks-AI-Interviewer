"""Candidate profile loader + day-selection helpers (Sections C, G)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from agent.config import settings
from agent.data.curriculum import load_curriculum
from agent.schemas import CandidateProfile


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_all_candidates() -> dict[str, CandidateProfile]:
    """Load candidate_profiles.json as {candidate_id: CandidateProfile}."""
    raw = _read_json(settings.candidate_profiles_path)
    if isinstance(raw, list):
        entries: list | dict = raw
    elif isinstance(raw, dict):
        entries = raw.get("candidates", raw)
    else:
        raise ValueError(f"Unexpected candidate_profiles.json structure: {type(raw)!r}")
    profiles: dict[str, CandidateProfile] = {}
    if isinstance(entries, dict):
        for cid, payload in entries.items():
            if isinstance(payload, dict):
                payload.setdefault("candidate_id", cid)
                profiles[cid] = CandidateProfile.model_validate(payload)
        return profiles
    for payload in entries:
        profile = CandidateProfile.model_validate(payload)
        profiles[profile.candidate_id] = profile
    return profiles


def load_candidate(candidate_id: str) -> CandidateProfile:
    """Load one candidate profile by ID, raising KeyError if missing."""
    return load_all_candidates()[candidate_id]


def day_status(profile: CandidateProfile, day_id: str) -> str:
    """Classify a day for a candidate: completed | skipped | unknown."""
    if day_id in profile.completed_missions:
        return "completed"
    if day_id in profile.skipped_topics:
        return "skipped"
    return "unknown"


def get_uncovered_days(
    profile: CandidateProfile, covered_days: list[str] | None = None
) -> list[str]:
    """Days available for questioning, ordered by Section G priority.

    Priority:
        1. Completed but not-yet-covered days (strength-probing).
        2. Skipped days (gentle probe, never a "gotcha").
        3. Remaining curriculum days.

    *covered_days* are days already asked about this session (excluded).
    The 70/30 completed-vs-skipped ratio policy is enforced separately in
    ``agent.fairness`` during question selection.
    """
    covered = set(covered_days or [])
    curriculum = load_curriculum()

    completed_uncovered = [
        d for d in profile.completed_missions if d in curriculum and d not in covered
    ]
    skipped = [d for d in profile.skipped_topics if d not in covered]
    unknown = [
        d
        for d in curriculum
        if d not in profile.completed_missions
        and d not in profile.skipped_topics
        and d not in covered
    ]
    return completed_uncovered + skipped + unknown