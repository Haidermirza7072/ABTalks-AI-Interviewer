"""Evaluation CLI: run all Section E metrics over session logs.

Usage:
    python -m agent.eval.run_all                    # all log files
    python -m agent.eval.run_all --session s1 s2    # specific sessions
    python -m agent.eval.run_all --bias             # + bias audit snapshot
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent.eval.metrics import bias_audit, evaluate_logs
from agent.logging import list_sessions, read_session_log


def load_all_records(only_sessions: list[str] | None = None) -> list[dict]:
    sessions = only_sessions or list_sessions()
    records: list[dict] = []
    for sid in sessions:
        records.extend(read_session_log(sid))
    return records


def nullable(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", nargs="*", default=None, help="session ids")
    parser.add_argument("--bias", action="store_true", help="run bias audit")
    parser.add_argument("--out", type=Path, default=None, help="write JSON report")
    args = parser.parse_args(argv)

    records = _load_relevant(args.session)
    report = evaluate_logs(records)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.bias:
        # Snapshot: profiles x readiness from the eval fixture (computed
        # by feeding the 5 candidate profiles through feedback synthesis).
        skipped = {
            "cand_001_anxious_alex": 1,
            "cand_002_maya_strong": 10,
            "cand_003_leo_gaps": 4,
            "cand_004_bias_probe_high": 20,
            "cand_005_bias_probe_low": 0,
        }
        readiness = {
            # Real values come from live feedback runs; these are placeholders
            # that the pytest suite overrides with computed scores.
            "cand_004_bias_probe_high": None,
        }
        r = bias_audit(skipped, readiness)
        print(f"Bias audit n={len(readiness)} (placeholder; live runs fill in): r={r:.3f}")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())