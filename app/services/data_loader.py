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
    """Load and validate curriculum.json into memory."""
    path = file_path or settings.CURRICULUM_FILE
    if not os.path.exists(path):
        logger.warning(f"Curriculum file not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    store = {}
    for idx, item in enumerate(data):
        try:
            day = CurriculumDay(**item)
            store[day.day_id] = day
        except ValidationError as e:
            raise ValueError(f"Schema mismatch in curriculum file at item index {idx}: {e}")

    return store


def load_candidate_profiles(file_path: str = None) -> Dict[str, CandidateProfile]:
    """Load and validate candidate_profiles.json into memory."""
    path = file_path or settings.CANDIDATE_FILE
    if not os.path.exists(path):
        logger.warning(f"Candidate profiles file not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    store = {}
    for idx, item in enumerate(data):
        try:
            profile = CandidateProfile(**item)
            store[profile.candidate_id] = profile
        except ValidationError as e:
            raise ValueError(f"Schema mismatch in candidate profiles file at item index {idx}: {e}")

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
