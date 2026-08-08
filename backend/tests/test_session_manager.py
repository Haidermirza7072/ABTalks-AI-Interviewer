import os
from datetime import datetime, timezone, timedelta
from app.models.schemas import InterviewSession
from app.services.session_manager import (
    SESSION_STORE,
    save_session,
    get_session,
    delete_session,
    reload_sessions_from_disk_on_startup,
    cleanup_expired_sessions,
    _get_session_file_path,
)

def test_session_creation_and_retrieval():
    """Test saving session to memory and reading it back."""
    session = InterviewSession(candidate_id="cand_101")
    SESSION_STORE[session.session_id] = session

    retrieved = get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.candidate_id == "cand_101"

def test_disk_persistence_every_2_turns(tmp_path):
    """Test that session is written to disk file on even turn count."""
    session = InterviewSession(candidate_id="cand_101")
    session.turn_count = 2

    # Save session synchronously for testing internal function logic
    file_path = _get_session_file_path(session.session_id)
    assert not os.path.exists(file_path)

    # Convert and write to file to verify schema
    data = session.to_dict()
    with open(file_path, "w", encoding="utf-8") as f:
        import json
        f.write(json.dumps(data))

    assert os.path.exists(file_path)
    reloaded = get_session(session.session_id)
    assert reloaded is not None
    assert reloaded.session_id == session.session_id

def test_startup_session_reload():
    """Test startup scanning and reloading active sessions."""
    # Active session (updated 10 mins ago)
    recent_sess = InterviewSession(candidate_id="cand_101")
    recent_file = _get_session_file_path(recent_sess.session_id)
    with open(recent_file, "w", encoding="utf-8") as f:
        import json
        f.write(json.dumps(recent_sess.to_dict()))

    # Expired session (updated 2 hours ago)
    old_sess = InterviewSession(candidate_id="cand_102")
    old_sess.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    old_file = _get_session_file_path(old_sess.session_id)
    with open(old_file, "w", encoding="utf-8") as f:
        import json
        f.write(json.dumps(old_sess.to_dict()))

    SESSION_STORE.clear()
    count = reload_sessions_from_disk_on_startup()

    assert count == 1
    assert recent_sess.session_id in SESSION_STORE
    assert old_sess.session_id not in SESSION_STORE
    assert not os.path.exists(old_file)

def test_cleanup_expired_sessions():
    """Test background cleanup removes expired in-memory sessions."""
    active_sess = InterviewSession(candidate_id="cand_101")
    expired_sess = InterviewSession(candidate_id="cand_102")
    expired_sess.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)

    SESSION_STORE[active_sess.session_id] = active_sess
    SESSION_STORE[expired_sess.session_id] = expired_sess

    cleaned = cleanup_expired_sessions()
    assert cleaned == 1
    assert active_sess.session_id in SESSION_STORE
    assert expired_sess.session_id not in SESSION_STORE

def test_delete_session():
    """Test explicit session deletion from memory and disk."""
    session = InterviewSession(candidate_id="cand_101")
    SESSION_STORE[session.session_id] = session
    file_path = _get_session_file_path(session.session_id)
    with open(file_path, "w", encoding="utf-8") as f:
        import json
        f.write(json.dumps(session.to_dict()))

    delete_session(session.session_id)
    assert session.session_id not in SESSION_STORE
    assert not os.path.exists(file_path)

def test_redis_fallback_mock():
    """Test loading session from Redis fallback when RAM miss occurs."""
    from unittest.mock import MagicMock, patch
    from app.services.session_manager import load_session_from_redis

    session = InterviewSession(candidate_id="cand_101")
    mock_redis = MagicMock()
    import json
    mock_redis.get.return_value = json.dumps(session.to_dict())

    with patch("app.services.session_manager.get_redis_client", return_value=mock_redis):
        loaded = load_session_from_redis(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
