"""Metrics over session logs (Section E) + bias audit (Section L).

Consumes the JSONL records written by ``agent.logging`` and computes
the Section E metric set:

    * Question Relevance  (>= 85%)
    * Follow-up Depth     (>= 80%, human review proxy: references_claim)
    * Feedback Schema Compliance (100%)
    * Evidence Anchoring  (>= 90%)
    * Question Type Diversity (>= 4 distinct types)
    * Hallucination Rate  (< 5%)
    * Persona balance     (no persona > 50%)
    * Fairness            (Pearson r < 0.5 between skipped-day count and
      readiness_score)
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

# ── simple helpers ──────────────────────────────────────────


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def pearson_r(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation coefficient; 0 when insufficient data."""
    n = len(xs)
    if n != len(ys) or n < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs) or 1.0)
    dy = math.sqrt(sum((y - my) ** 2 for y in ys) or 1.0)
    return num / (dx * dy)


# ── per-metric evaluators ───────────────────────────────────


def question_relevance(records: list[dict]) -> float:
    """Fraction of logged questions with relevance_score >= threshold."""
    scored = [r for r in records if r.get("relevance_score") is not None]
    if not scored:
        return 0.0
    from agent.config import settings

    hits = sum(1 for r in scored if r["relevance_score"] >= settings.relevance_threshold)
    return hits / len(scored)


def followup_depth(records: list[dict]) -> float:
    """Proxy for 'references a specific claim': actual_type == expected or
    a references_claim is present.  (Human review replaces this in the
    final checkpoint; Section E.)"""
    followups = [r for r in records if r.get("task") == "generate_followup"]
    if not followups:
        return 0.0
    anchored = sum(
        1 for r in followups if (r.get("references_claim") or "").strip()
    )
    return anchored / len(followups)


def schema_compliance(records: list[dict]) -> float:
    """Fraction of runs that passed schema+content validation."""
    judged = [r for r in records if r.get("validation_passed") is not None]
    if not judged:
        return 0.0
    return sum(1 for r in judged if r["validation_passed"]) / len(judged)


def evidence_anchoring(records: list[dict]) -> float:
    """Fraction of feedback runs that passed citation anchoring."""
    fb = [r for r in records if r.get("task") == "synthesize_feedback"]
    if not fb:
        return 0.0
    anchored = sum(1 for r in fb if r.get("validation_passed"))
    return anchored / len(fb)


def type_diversity(records: list[dict]) -> float:
    """Average distinct question types per session (target >= 4)."""
    by_session: dict[str, set] = defaultdict(set)
    for r in records:
        if r.get("actual_type"):
            by_session[r.get("session_id", "?")].add(r["actual_type"])
    if not by_session:
        return 0.0
    return _mean([len(s) for s in by_session.values()])


def hallucination_rate(records: list[dict]) -> float:
    """Fraction of question records with hallucination warnings."""
    q = [r for r in records if r.get("task") in ("generate_question", "generate_followup")]
    if not q:
        return 0.0
    warned = sum(1 for r in q if (r.get("extra") or {}).get("hallucination_warnings"))
    return warned / len(q)


def persona_balance(records: list[dict]) -> dict[str, float]:
    """Persona -> share of turns; None-safe for missing persona."""
    counter = Counter(r.get("persona") or "unknown" for r in records)
    total = sum(counter.values()) or 1
    return {k: v / total for k, v in counter.items()}


# ── aggregate report ────────────────────────────────────────


def evaluate_logs(records: list[dict]) -> dict:
    """Full Section E metric report over a set of log records."""
    from agent.config import settings

    balance = persona_balance(records)
    return {
        "question_relevance": round(question_relevance(records), 3),
        "followup_depth": round(followup_depth(records), 3),
        "schema_compliance": round(schema_compliance(records), 3),
        "evidence_anchoring": round(evidence_anchoring(records), 3),
        "type_diversity_avg": round(type_diversity(records), 2),
        "hallucination_rate": round(hallucination_rate(records), 3),
        "persona_balance": balance,
        "persona_dominance_violated": any(
            v > settings.persona_dominance_cap for v in balance.values()
        ),
        "total_records": len(records),
    }


def bias_audit(
    profiles_skipped: dict[str, int],
    readiness_scores: dict[str, float | None],
) -> float:
    """Pearson r between skipped-day count and readiness (Section L).

    Acceptance: |r| < 0.5.
    """
    xs: list[float] = []
    ys: list[float] = []
    for cid, skipped in profiles_skipped.items():
        score = readiness_scores.get(cid)
        if score is None:
            continue
        xs.append(float(skipped))
        ys.append(float(score))
    return pearson_r(xs, ys)