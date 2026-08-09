import json
import logging
import os
from typing import Dict, List, Tuple
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import CandidateProfile, CurriculumDay

logger = logging.getLogger(__name__)

# Global in-memory repositories
CURRICULUM_STORE: Dict[str, CurriculumDay] = {}
CANDIDATE_STORE: Dict[str, CandidateProfile] = {}
FALLBACK_QUESTIONS: Dict[str, List[str]] = {}


def load_curriculum(file_path: str = None) -> Dict[str, CurriculumDay]:
    """Load and validate curriculum.json into memory.

    Handles both formats:
    - List of CurriculumDay dicts (flat format)
    - Dict with 'days' key containing raw day objects (ABTalks format)
    """
    path = file_path or settings.CURRICULUM_FILE
    if not os.path.exists(path):
        logger.warning(f"Curriculum file not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle ABTalks format: { "cohort": ..., "modules": ..., "days": [...] }
    if isinstance(data, dict) and "days" in data:
        raw_days = data["days"]
    elif isinstance(data, list):
        raw_days = data
    else:
        logger.warning(f"Unexpected curriculum format in {path}")
        return {}

    store = {}
    for idx, item in enumerate(raw_days):
        try:
            if not isinstance(item, dict):
                continue  # skip non-dict entries

            # Normalize field names from ABTalks format
            if "day" in item and "day_id" not in item:
                item["day_id"] = f"day_{item['day']:02d}"
            if "objectives" in item and "learning_objectives" not in item:
                item["learning_objectives"] = item.pop("objectives")
            if "topics" not in item:
                item["topics"] = []

            # Remove extra fields that CurriculumDay doesn't expect
            known_fields = {"day_id", "title", "topics", "learning_objectives", "tools", "prerequisites"}
            cleaned = {k: v for k, v in item.items() if k in known_fields}

            day = CurriculumDay(**cleaned)
            store[day.day_id] = day
        except (ValidationError, KeyError, TypeError) as e:
            logger.warning(f"Skipping curriculum item {idx}: {e}")

    return store


def _normalize_candidate(raw: dict) -> dict:
    """Normalize ABTalks candidate format to CandidateProfile fields.

    ABTalks format:
        {
            "member": {"id": "CAND-001", "name": "...", ...},
            "missions": [{"day": 7, "passed": true, "attempts": 1}, ...],
            "signals": {"commitDays": 28, ...}
        }

    Backend CandidateProfile expects:
        candidate_id, completed_missions, skipped_topics, attempts, tools_used, learning_signals
    """
    member = raw.get("member", {})
    missions = raw.get("missions", [])
    signals = raw.get("signals", {})

    candidate_id = member.get("id", "unknown")

    completed = []
    skipped = []
    attempts = {}
    for m in missions:
        day_id = f"day_{m['day']:02d}"
        if m.get("passed", False):
            completed.append(day_id)
        else:
            skipped.append(day_id)
        if "attempts" in m:
            attempts[day_id] = m["attempts"]

    return {
        "candidate_id": candidate_id,
        "completed_missions": completed,
        "skipped_topics": skipped,
        "attempts": attempts,
        "tools_used": [],
        "learning_signals": signals,
    }


def load_candidate_profiles(file_path: str = None) -> Dict[str, CandidateProfile]:
    """Load and validate candidate_profiles.json into memory.

    Handles both formats:
    - List of CandidateProfile dicts (flat format)
    - Dict with 'candidates' key (ABTalks format)
    """
    path = file_path or settings.CANDIDATE_FILE
    if not os.path.exists(path):
        logger.warning(f"Candidate profiles file not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle ABTalks format: { "candidates": [...] }
    if isinstance(data, dict) and "candidates" in data:
        raw_candidates = data["candidates"]
    elif isinstance(data, list):
        raw_candidates = data
    else:
        logger.warning(f"Unexpected candidate profiles format in {path}")
        return {}

    store = {}
    for idx, item in enumerate(raw_candidates):
        try:
            if not isinstance(item, dict):
                continue

            # Normalize if ABTalks format (has 'member' key)
            if "member" in item:
                item = _normalize_candidate(item)

            profile = CandidateProfile(**item)
            store[profile.candidate_id] = profile
        except (ValidationError, KeyError, TypeError) as e:
            logger.warning(f"Skipping candidate profile {idx}: {e}")

    return store


def load_fallback_questions(file_path: str = None) -> Dict[str, List[str]]:
    """Load fallback questions from JSON file."""
    path = file_path or settings.FALLBACK_FILE
    if not os.path.exists(path):
        logger.warning(f"Fallback questions file not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def init_data_stores() -> Tuple[int, int]:
    """Initializes global data stores from disk. Returns count of (days, candidates)."""
    global CURRICULUM_STORE, CANDIDATE_STORE, FALLBACK_QUESTIONS
    CURRICULUM_STORE.clear()
    CURRICULUM_STORE.update(load_curriculum())

    CANDIDATE_STORE.clear()
    CANDIDATE_STORE.update(load_candidate_profiles())

    FALLBACK_QUESTIONS.clear()
    FALLBACK_QUESTIONS.update(load_fallback_questions())

    logger.info(f"Loaded {len(CURRICULUM_STORE)} curriculum days and {len(CANDIDATE_STORE)} candidates.")
    return len(CURRICULUM_STORE), len(CANDIDATE_STORE)
