import pytest
import json
from app.services.data_loader import (
    load_curriculum,
    load_candidate_profiles,
    load_fallback_questions,
)

def test_load_non_existent_files():
    """Test loading non-existent file returns empty dictionary."""
    assert load_curriculum("non_existent.json") == {}
    assert load_candidate_profiles("non_existent.json") == {}
    assert load_fallback_questions("non_existent.json") == {}

def test_load_curriculum_invalid_schema(tmp_path):
    """Test invalid curriculum items are skipped gracefully."""
    bad_file = tmp_path / "bad_curriculum.json"
    bad_file.write_text(json.dumps([{"invalid_field": "data"}]), encoding="utf-8")

    # Invalid items are now skipped, not raised
    result = load_curriculum(str(bad_file))
    assert result == {}

def test_load_candidate_profiles_invalid_schema(tmp_path):
    """Test invalid candidate items are skipped gracefully."""
    bad_file = tmp_path / "bad_candidate.json"
    bad_file.write_text(json.dumps([{"invalid_field": "data"}]), encoding="utf-8")

    # Invalid items are now skipped, not raised
    result = load_candidate_profiles(str(bad_file))
    assert result == {}

def test_load_curriculum_abtalks_format(tmp_path):
    """Test loading ABTalks curriculum format with nested days."""
    data = {
        "cohort": "Test Cohort",
        "modules": [],
        "days": [
            {"day": 1, "title": "Setup", "tools": ["Python"], "objectives": ["Install Python"]},
            {"day": 2, "title": "Basics", "tools": ["VS Code"], "objectives": ["Learn syntax"]},
        ]
    }
    f = tmp_path / "curriculum.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    result = load_curriculum(str(f))
    assert len(result) == 2
    assert "day_01" in result
    assert result["day_01"].title == "Setup"
    assert result["day_01"].learning_objectives == ["Install Python"]

def test_load_candidate_profiles_abtalks_format(tmp_path):
    """Test loading ABTalks candidate format with nested member/missions."""
    data = {
        "candidates": [
            {
                "member": {"id": "CAND-001", "name": "Test User"},
                "missions": [
                    {"day": 1, "title": "Setup", "passed": True, "attempts": 1},
                    {"day": 2, "title": "Basics", "passed": False, "attempts": 3},
                ],
                "signals": {"commitDays": 5}
            }
        ]
    }
    f = tmp_path / "candidates.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    result = load_candidate_profiles(str(f))
    assert len(result) == 1
    assert "CAND-001" in result
    p = result["CAND-001"]
    assert "day_01" in p.completed_missions
    assert "day_02" in p.skipped_topics
    assert p.attempts["day_01"] == 1
