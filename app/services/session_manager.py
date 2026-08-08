import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
try:
    import aiofiles
except ImportError:
    aiofiles = None

from app.config import settings
from app.models.schemas import InterviewSession

logger = logging.getLogger(__name__)

# Primary in-memory store
SESSION_STORE: Dict[str, InterviewSession] = {}

# Redis client placeholder if redis is configured
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None and settings.REDIS_URL:
        try:
            import redis
            _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")
            _redis_client = None
    return _redis_client


def ensure_session_dir():
    """Ensure the filesystem session persistence directory exists."""
    os.makedirs(settings.SESSION_DIR, exist_ok=True)


def _get_session_file_path(session_id: str) -> str:
    ensure_session_dir()
    return os.path.join(settings.SESSION_DIR, f"{session_id}.json")


def _write_session_sync(file_path: str, content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


async def persist_session_to_disk(session: InterviewSession) -> None:
    """Asynchronously persist session to disk JSON file."""
    try:
        ensure_session_dir()
        file_path = _get_session_file_path(session.session_id)
        data = session.to_dict()
        json_str = json.dumps(data, indent=2)
        if aiofiles is not None:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json_str)
        else:
            await asyncio.to_thread(_write_session_sync, file_path, json_str)
        logger.debug(f"Persisted session {session.session_id} to disk.")
    except Exception as e:
        logger.error(f"Failed to persist session {session.session_id} to disk: {e}")


def persist_session_to_redis(session: InterviewSession) -> None:
    """Mirror session state to Redis if available with 2-hour TTL."""
    client = get_redis_client()
    if client:
        try:
            key = f"session:{session.session_id}"
            data = json.dumps(session.to_dict())
            client.setex(key, 7200, data)  # 2 hours TTL
        except Exception as e:
            logger.warning(f"Failed to save session to Redis: {e}")


def load_session_from_redis(session_id: str) -> Optional[InterviewSession]:
    """Retrieve session from Redis if available."""
    client = get_redis_client()
    if client:
        try:
            key = f"session:{session_id}"
            data_str = client.get(key)
            if data_str:
                data = json.loads(data_str)
                return InterviewSession.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load session from Redis: {e}")
    return None


def load_session_from_disk(session_id: str) -> Optional[InterviewSession]:
    """Load session from disk file if exists."""
    file_path = _get_session_file_path(session_id)
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        session = InterviewSession.from_dict(data)
        return session
    except Exception as e:
        logger.error(f"Failed to load session from disk at {file_path}: {e}")
        return None


def get_session(session_id: str) -> Optional[InterviewSession]:
    """
    Multi-layer state resolution:
    1. In-memory Dict
    2. Redis (if available)
    3. Disk filesystem
    """
    # 1. Check RAM
    if session_id in SESSION_STORE:
        return SESSION_STORE[session_id]

    # 2. Check Redis
    session = load_session_from_redis(session_id)
    if session:
        SESSION_STORE[session_id] = session
        return session

    # 3. Check Filesystem
    session = load_session_from_disk(session_id)
    if session:
        SESSION_STORE[session_id] = session
        return session

    return None


async def save_session(session: InterviewSession) -> None:
    """Update session state in memory, and persist every 2 turns or status change."""
    session.updated_at = datetime.now(timezone.utc)
    SESSION_STORE[session.session_id] = session

    # Redis mirror
    persist_session_to_redis(session)

    # Persist to disk every 2 turns or when session concludes/aborts
    if session.turn_count % 2 == 0 or session.status in ("completed", "aborted"):
        await persist_session_to_disk(session)


def delete_session(session_id: str) -> None:
    """Remove session from memory, Redis, and disk."""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]

    client = get_redis_client()
    if client:
        try:
            client.delete(f"session:{session_id}")
        except Exception:
            pass

    file_path = _get_session_file_path(session_id)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove session file {file_path}: {e}")


def reload_sessions_from_disk_on_startup() -> int:
    """
    On application startup, scan session dir and reload sessions with updated_at < 1 hour ago.
    Purge older session files.
    """
    ensure_session_dir()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=settings.SESSION_TTL_HOURS)
    reloaded_count = 0

    if not os.path.exists(settings.SESSION_DIR):
        return 0

    for filename in os.listdir(settings.SESSION_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(settings.SESSION_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session = InterviewSession.from_dict(data)
                
                # Check if updated_at is within 1 hour
                sess_updated = session.updated_at
                if sess_updated.tzinfo is None:
                    sess_updated = sess_updated.replace(tzinfo=timezone.utc)

                if sess_updated >= one_hour_ago:
                    SESSION_STORE[session.session_id] = session
                    reloaded_count += 1
                else:
                    # Expired, delete file
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error restoring session from file {filename}: {e}")

    logger.info(f"Reloaded {reloaded_count} active sessions from disk on startup.")
    return reloaded_count


def cleanup_expired_sessions() -> int:
    """Background task logic to purge expired sessions (> 1 hour old)."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=settings.SESSION_TTL_HOURS)
    expired_ids = []

    for sid, sess in list(SESSION_STORE.items()):
        sess_updated = sess.updated_at
        if sess_updated.tzinfo is None:
            sess_updated = sess_updated.replace(tzinfo=timezone.utc)
        if sess_updated < cutoff:
            expired_ids.append(sid)

    for sid in expired_ids:
        logger.info(f"Cleaning up expired session {sid}")
        delete_session(sid)

    return len(expired_ids)
