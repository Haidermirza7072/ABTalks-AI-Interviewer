"""Lightweight JSONL session logger for continuous improvement (Section H).

Each pipeline run appends one JSON line to
``{log_dir}/{session_id}.jsonl`` capturing the inputs, output, validation
result, fallback usage, and latency. The eval suite (Feature 13) and
checkpoint reviews consume these logs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from agent.config import settings


def _ensure_log_dir() -> Path:
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Fallback for permission errors (e.g. /tmp on Windows).
        fallback = settings.project_root / "interview_logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    return settings.log_dir


def log_run(
    *,
    session_id: str,
    candidate_id: str,
    task: str,
    question: str | None,
    expected_type: str | None,
    actual_type: str | None,
    relevance_score: float | None,
    validation_passed: bool,
    fallback_used: bool,
    persona: str | None = None,
    latency_ms: int | None = None,
    failure_reasons: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append one structured record to the session's JSONL log file."""
    record: dict[str, Any] = {
        "ts": time.time(),
        "session_id": session_id,
        "candidate_id": candidate_id,
        "task": task,
        "question": question,
        "expected_type": expected_type,
        "actual_type": actual_type,
        "relevance_score": relevance_score,
        "validation_passed": validation_passed,
        "fallback_used": fallback_used,
        "persona": persona,
        "latency_ms": latency_ms,
        "failure_reasons": failure_reasons or [],
    }
    if extra:
        record.update(extra)

    log_dir = _ensure_log_dir()
    path = log_dir / f"{session_id}.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_session_log(session_id: str) -> list[dict[str, Any]]:
    """Load all records for a given session (used by eval suite)."""
    log_dir = _ensure_log_dir()
    path = log_dir / f"{session_id}.jsonl"
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def list_sessions() -> list[str]:
    """Return session IDs that have log files (for checkpoint reviews)."""
    log_dir = _ensure_log_dir()
    return sorted(p.stem for p in log_dir.glob("*.jsonl"))
