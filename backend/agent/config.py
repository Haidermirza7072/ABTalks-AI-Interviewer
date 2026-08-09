"""Centralized configuration.

Policies live here as hardcoded defaults so they are versioned and
reviewable in one place.  The ONLY environment variable that matters
is ``OPENROUTER_API_KEY`` (loaded from .env) — everything else is
tunable in this file, matching Member 3 spec Sections D & F.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    """Sampling + latency config for one cognitive task."""

    temperature: float
    top_p: float
    max_tokens: int
    timeout_seconds: int


@dataclass(frozen=True)
class Settings:
    # --- OpenRouter connection (secret comes from .env only) ---
    openrouter_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", "")
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # --- Models ---
    primary_model: str = "meta-llama/llama-3.3-70b-instruct"
    fallback_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    embedding_model: str = "openai/text-embedding-3-small"

    # --- Task-specific configs (Section D / F) ---
    question_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            timeout_seconds=5,
        )
    )
    followup_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            timeout_seconds=5,
        )
    )
    feedback_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            temperature=0.3,
            top_p=0.95,
            max_tokens=2048,
            timeout_seconds=25,
        )
    )
    summarize_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            temperature=0.2,
            top_p=0.95,
            max_tokens=512,
            timeout_seconds=10,
        )
    )
    score_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            temperature=0.2,
            top_p=0.95,
            max_tokens=512,
            timeout_seconds=25,
        )
    )

    # --- Paths ---
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    data_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data"
    )
    curriculum_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "data"
        / "curriculum.json"
    )
    candidate_profiles_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "data"
        / "candidate_profiles.json"
    )
    fallback_bank_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent
        / "data"
        / "fallback_questions.json"
    )
    log_dir: Path = field(
        default_factory=lambda: Path("/tmp/interview_logs")
    )

    # --- Validation thresholds (Section E) ---
    relevance_threshold: float = 0.65
    evidence_anchoring_target: float = 0.90
    hallucination_rate_cap: float = 0.05
    max_recent_question_types: int = 3
    min_distinct_types_per_interview: int = 4
    context_window_turn_threshold: int = 6
    context_window_keep_recent: int = 4

    # --- Bias targets (Section H) ---
    persona_dominance_cap: float = 0.50
    completed_day_target_ratio: float = 0.70
    bias_correlation_cap: float = 0.50

    # --- Follow-up activation (Section I) ---
    followup_score_threshold: float = 7.0
    followup_skip_forcing_ratio: float = 0.50


settings = Settings()