"""Unit-level tests (Section L): taxonomy, follow-up activation, metrics."""
import math

import pytest

from agent.eval.metrics import pearson_r
from agent.schemas import QuestionType
from agent.taxonomy import (
    QuestionTypeQueue,
    should_generate_followup,
)


class TestQuestionTypeQueue:
    def test_records_types(self):
        q = QuestionTypeQueue()
        q.record("challenge")
        q.record(QuestionType.EXPAND)
        assert q.recent == [QuestionType.CHALLENGE, QuestionType.EXPAND]
        assert q.as_list() == ["challenge", "expand"]

    def test_rolling_window(self):
        q = QuestionTypeQueue(window=2)
        for t in ["challenge", "expand", "compare"]:
            q.record(t)
        assert [t.value for t in q.recent] == ["expand", "compare"]

    def test_no_repeat_within_two(self):
        q = QuestionTypeQueue(window=3)
        q.record("challenge")
        q.record("expand")
        assert not q.is_allowed("challenge")
        assert not q.is_allowed("expand")
        assert q.is_allowed("compare")
        assert q.forbidden_types() == [QuestionType.CHALLENGE, QuestionType.EXPAND]

    def test_repeat_allowed_after_two_turns(self):
        q = QuestionTypeQueue(window=3)
        q.record("challenge")
        q.record("expand")
        q.record("meta")
        assert q.is_allowed("challenge")

    def test_diversity_metric(self):
        q = QuestionTypeQueue(window=3)
        q.record("challenge")
        assert not q.diversity_satisfied()
        for t in ["expand", "meta", "compare"]:
            q.record(t)
        assert q.diversity_satisfied()
        assert q.distinct_count() == 4


class TestFollowupActivation:
    def test_high_score_triggers(self):
        assert should_generate_followup(
            latest_score=8.0, validation_passed=True, skip_ratio=0.0
        )

    def test_low_score_withholds(self):
        assert not should_generate_followup(
            latest_score=5.0, validation_passed=True, skip_ratio=0.0
        )

    def test_failed_validation_never_triggers(self):
        assert not should_generate_followup(
            latest_score=9.0, validation_passed=False, skip_ratio=0.8
        )

    def test_forced_by_heavy_skipping(self):
        assert should_generate_followup(
            latest_score=5.0, validation_passed=True, skip_ratio=0.6
        )

    def test_missing_score_no_trigger(self):
        assert not should_generate_followup(
            latest_score=None, validation_passed=True, skip_ratio=0.0
        )


class TestPearson:
    def test_perfect_positive(self):
        assert abs(pearson_r([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9

    def test_perfect_negative(self):
        assert abs(pearson_r([1, 2, 3], [6, 4, 2]) + 1.0) < 1e-9

    def test_flat_series_returns_zero(self):
        assert pearson_r([1, 2, 3], [5, 5, 5]) == 0.0

    def test_short_series_returns_zero(self):
        assert pearson_r([7], [8]) == 0.0
        assert pearson_r([], []) == 0.0