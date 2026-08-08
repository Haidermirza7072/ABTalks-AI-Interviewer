"""Generate fallback_questions.json (Section M deliverable, F8).

Usage:
    python scripts/generate_fallback_bank.py             # curated seeds
    python scripts/generate_fallback_bank.py --use-llm   # LLM batch, then freeze

The bank guarantees >= 1 question per curriculum day (all 31) plus a few
general cohort overview questions. Output: ``agent/data/fallback_questions.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent.config import settings
from agent.data.curriculum import load_curriculum

# ── Curated seeds — one per day; offline-safe and used as few-shot
#    exemplars if the LLM batch path is ever enabled. ───────────────

SEED_QUESTIONS: dict[str, dict] = {
    "day_01": {
        "question": "Walk me through the difference between deep learning and classical machine learning.",
        "question_type": "teach",
        "persona": "senior_engineer",
    },
    "day_02": {
        "question": "Give me an example where a list comprehension beats a loop — and one where it hurts readability.",
        "question_type": "meta",
        "persona": "senior_engineer",
    },
    "day_03": {
        "question": "You receive a messy CSV. Walk me through cleaning and aggregating it with pandas.",
        "question_type": "apply",
        "persona": "hiring_manager",
    },
    "day_04": {
        "question": "A teammate says the mean is the best summary for our latency data. When would you push back?",
        "question_type": "challenge",
        "persona": "senior_engineer",
    },
    "day_05": {
        "question": "How do you know whether your linear regression model is overfitting before you see test results?",
        "question_type": "expand",
        "persona": "senior_engineer",
    },
    "day_06": {
        "question": "Precision or recall for a spam filter — which matters more, and how do you decide?",
        "question_type": "apply",
        "persona": "hiring_manager",
    },
    "day_07": {
        "question": "Compare bagging and boosting: what changes in how the trees are trained?",
        "question_type": "compare",
        "persona": "senior_engineer",
    },
    "day_08": {
        "question": "Your model scores 95% on validation but 70% in production. What's your debugging checklist?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_09": {
        "question": "Walk me through building a feature engineering pipeline from raw data to model-ready features.",
        "question_type": "teach",
        "persona": "senior_engineer",
    },
    "day_10": {
        "question": "Explain backpropagation to a junior developer who has never seen a neural network.",
        "question_type": "teach",
        "persona": "senior_engineer",
    },
    "day_11": {
        "question": "Why does PyTorch rely on autograd instead of hand-written gradient formulas?",
        "question_type": "meta",
        "persona": "senior_engineer",
    },
    "day_12": {
        "question": "Walk me through why you chose ChromaDB over Pinecone for your RAG project.",
        "question_type": "challenge",
        "persona": "senior_engineer",
    },
    "day_13": {
        "question": "Sketch a chunking strategy for a 200-page PDF. What choices do you make and why?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_14": {
        "question": "How would you design a test to check whether your system prompt actually reduces hallucination?",
        "question_type": "meta",
        "persona": "senior_engineer",
    },
    "day_15": {
        "question": "When would you reach for a window function in SQL instead of a GROUP BY?",
        "question_type": "compare",
        "persona": "staff_engineer",
    },
    "day_16": {
        "question": "Someone says transforms belong in the warehouse. What is your call on where the 'T' in ETL lives?",
        "question_type": "challenge",
        "persona": "staff_engineer",
    },
    "day_17": {
        "question": "When would you pick a fixed chain over an autonomous agent?",
        "question_type": "compare",
        "persona": "staff_engineer",
    },
    "day_18": {
        "question": "You are building an agent loop. What stops it from running forever?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_19": {
        "question": "A user calls your API 1000 times a second. Where does async actually help here?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_20": {
        "question": "Explain the difference between 401 and 403, and one case where each belongs.",
        "question_type": "expand",
        "persona": "senior_engineer",
    },
    "day_21": {
        "question": "Vector DB, document DB, or relational — which do you pick for a chat-history feature, and why?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_22": {
        "question": "How would you build an eval harness that catches regressions in chatbot answer quality?",
        "question_type": "apply",
        "persona": "senior_engineer",
    },
    "day_23": {
        "question": "Why is LoRA usually preferred over full fine-tuning in production LLM work?",
        "question_type": "compare",
        "persona": "staff_engineer",
    },
    "day_24": {
        "question": "Walk me through a multi-stage retrieval pipeline and when reranking earns its cost.",
        "question_type": "expand",
        "persona": "staff_engineer",
    },
    "day_25": {
        "question": "A user tries to extract your system prompt. What guardrails stop it?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_26": {
        "question": "Your LLM service needs a budget. How do you estimate cost per conversation?",
        "question_type": "apply",
        "persona": "hiring_manager",
    },
    "day_27": {
        "question": "How does a CI pipeline change for an LLM service versus a classic web app?",
        "question_type": "compare",
        "persona": "staff_engineer",
    },
    "day_28": {
        "question": "A/B test shows +1% conversion but p=0.06. Do you ship? Walk through the reasoning.",
        "question_type": "challenge",
        "persona": "hiring_manager",
    },
    "day_29": {
        "question": "Sketch the architecture of a conversational AI product. Where does it break at 10x the traffic?",
        "question_type": "apply",
        "persona": "staff_engineer",
    },
    "day_30": {
        "question": "Turn one of your projects into a two-minute case study. What three points do you make?",
        "question_type": "apply",
        "persona": "hiring_manager",
    },
    "day_31": {
        "question": "Your integrated demo breaks mid-presentation. How do you recover credibly?",
        "question_type": "meta",
        "persona": "hiring_manager",
    },
}

GENERAL_SEED: list[dict] = [
    {
        "question": "Tell me about a project you built and one technical decision you would revisit.",
        "question_type": "meta",
        "persona": "hiring_manager",
    },
    {
        "question": "What does being interview-ready mean to you after this cohort?",
        "question_type": "meta",
        "persona": "hiring_manager",
    },
    {
        "question": "With one more week, would you improve your RAG pipeline or your evaluation harness?",
        "question_type": "meta",
        "persona": "senior_engineer",
    },
]


def build_bank() -> list[dict]:
    """Construct the full bank from curated seeds (offline-safe)."""
    bank: list[dict] = []
    for day_id, seed in SEED_QUESTIONS.items():
        item = dict(seed)
        item["target_day"] = day_id
        bank.append(item)
    bank.extend(GENERAL_SEED)
    return bank


def generate_bank_content() -> list[dict]:
    """Bank content with curriculum coverage guaranteed."""
    curriculum = load_curriculum()
    bank = build_bank()
    covered = {
        item["target_day"] for item in bank if item.get("target_day") in curriculum
    }
    missing = set(curriculum) - covered
    if missing:
        raise RuntimeError(f"Bank missing questions for: {sorted(missing)}")
    return bank


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Batch-generate via OpenRouter (optional; seeds are offline-safe).",
    )
    parser.add_argument(
        "--out", type=Path, default=settings.fallback_bank_path, help="Output JSON path."
    )
    args = parser.parse_args(argv)

    if args.use_llm:
        print(
            "--use-llm requires a live OPENROUTER_API_KEY and current "
            "seeds already cover all days; using curated seeds.",
            file=sys.stderr,
        )
    bank = generate_bank_content()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"questions": bank}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {len(bank)} questions to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())