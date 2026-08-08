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
    """Test ValueError is raised when curriculum JSON has invalid schema."""
    bad_file = tmp_path / "bad_curriculum.json"
    bad_file.write_text(json.dumps([{"invalid_field": "data"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="Schema mismatch in curriculum file"):
        load_curriculum(str(bad_file))

def test_load_candidate_profiles_invalid_schema(tmp_path):
    """Test ValueError is raised when candidate profiles JSON has invalid schema."""
    bad_file = tmp_path / "bad_candidate.json"
    bad_file.write_text(json.dumps([{"invalid_field": "data"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="Schema mismatch in candidate profiles file"):
        load_candidate_profiles(str(bad_file))
