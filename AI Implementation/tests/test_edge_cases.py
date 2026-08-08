"""Edge-case and robustness tests (Section L edge cases)."""
import pytest

from agent.context import window_history
from agent.eval.metrics import evaluate_logs
from agent.pipeline import AgentPipeline
from agent.schemas import ConversationTurn
from tests.fixtures.mock_client import FakeLLM


def _turns(n: int) -> list[ConversationTurn]:
    return [ConversationTurn(role="candidate", content=f"a{i}", turn=i)
            for i in range(n)]


class TestWindowing:
    def test_history_kept_under_threshold(self):
        turns = _turns(4)
        windowed, used_summary = window_history(turns)
        assert len(windowed) == 4
        assert used_summary is False

    def test_window_trims_old_turns(self):
        turns = _turns(20)
        windowed, used_summary = window_history(turns)
        assert len(windowed) == 4
        assert windowed[-1].content == "a19"
        assert used_summary is False

    def test_empty_history(self):
        assert window_history([]) == ([], False)

    def test_summary_prepended_when_truncating(self):
        turns = _turns(20)
        windowed, used_summary = window_history(turns, summary="earlier turns")
        assert used_summary is True
        assert "[Summary of earlier turns]" in windowed[0].content
        assert len(windowed) == 5  # summary turn + keep_recent


class TestEvalMetricsEdge:
    def test_empty_records(self):
        report = evaluate_logs([])
        assert report["total_records"] == 0
        assert report["question_relevance"] == 0.0

    def test_no_question_records(self):
        report = evaluate_logs(
            [{"task": "summarize", "validation_passed": True}]
        )
        assert report["followup_depth"] == 0.0
        assert report["type_diversity_avg"] == 0.0


@pytest.mark.asyncio
async def test_unknown_task_rejected(profile_alex, make_request):
    pipe = AgentPipeline(client=FakeLLM())
    with pytest.raises(Exception):
        await pipe.run(make_request("bake_cake", profile_alex))