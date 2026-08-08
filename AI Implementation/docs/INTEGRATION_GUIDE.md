# The Thread Puller — Agent Integration Guide (F16)

Quickstart for **Member 2 (backend)**: how to call the AI agent from your
FastAPI service, what it returns, and how to run tests.  The agent runs
fully offline: with no API key it degrades gracefully — questions fall
back to the offline bank, feedback to a partial template.  Add an
`OPENROUTER_API_KEY` to enable real model calls.

---

## 1. Run everything with Docker (recommended)

```bash
# build the agent image
docker compose build agent

# run the full test suite (offline, no API key needed)
docker run --rm -v "%CD%\agent:/app/agent:ro" -v "%CD%\tests:/app/tests:ro" threadpuller-agent:latest -m pytest tests -q

# smoke the pipeline with the offline eval-replay (no HTTP)
docker run --rm -v "%CD%\scripts:/app/scripts" threadpuller-agent:latest /app/scripts/smoke_pipeline.py
```

The image's entrypoint is `python` (see `Dockerfile`), so the second and
third commands work directly.

## 2. The one function you need

```python
from agent.pipeline import run_agent
from agent.schemas import AgentRequest, SessionMetadata

result = await run_agent(request)
```

`run_agent` is the only public entry point (`agent/pipeline.py` bottom).
Everything else is internal.

### Building an AgentRequest

```python
from agent.schemas import (
    AgentRequest,
    CandidateProfile,
    ConversationTurn,
    EvidenceEntry,
    SessionMetadata,
)

request = AgentRequest(
    task="generate_question",          # see TaskType below
    candidate_profile=CandidateProfile(
        candidate_id="cand_abc",
        completed_missions=["day_01", "day_02", "day_03"],
        skipped_topics=["day_04"],
        tools_used=["Python", "ChromaDB"],
    ),
    conversation_history=[
        ConversationTurn(role="candidate", content="I built a RAG pipeline.", turn=1),
    ],
    session_metadata=SessionMetadata(
        session_id="sess_xyz",         # write your own id here
        turn_count=3,
        covered_days=["day_01"],
        current_persona="senior_engineer",
    ),
    evidence_log=[EvidenceEntry(topic="RAG", signal="strong", evidence="...")],
)
```

### Supported tasks (`TaskType`)

| task                    | output type      | notes                                     |
| ----------------------- | ---------------- | ----------------------------------------- |
| `generate_question`     | `QuestionOutput` | new interview question (target_day filled)|
| `generate_followup`     | `QuestionOutput` | follow-up on the last answer              |
| `synthesize_feedback`   | `FeedbackReport` | readiness score + strengths/growth areas  |
| `summarize`             | `SummaryOutput`  | running transcript summary                |

### Return contract (`AgentOutput`)

```python
{
  "task": "generate_question",
  "output": {...},                  # typed per task (QuestionOutput etc.)
  "fallback_used": false,           # true when the question bank had to serve
  "validation_passed": true,        # false → treat output with care
  "failure_reasons": [],            # what failed, if anything
  "latency_ms": 412
}
```

**Important:** always render `failure_reasons` (or
`validation_passed == False`) as a "try again" signal in the UI, and
fall back to your own canned copy when `fallback_used` is true.

## 3. Configuration

**`.env` holds secrets only** — currently just the API key.  Every other
setting (models, thresholds, timeouts, paths) is hardened in
`agent/config.py`; copy `.env.example` to `.env` and fill the key.

| var                  | note                                             |
| -------------------- | ------------------------------------------------ |
| `OPENROUTER_API_KEY` | empty → offline fallback mode; set → real LLM   |

Everything else: `agent/config.py` → `Settings` dataclass
(`primary_model`, `question_config.temperature`, `log_dir`, ...).

## 4. Data files (member 1 owns these; do not edit lightly)

- `data/curriculum.json` — 31-day cohort curriculum
- `data/candidate_profiles.json` — seed candidate profiles
- `agent/data/fallback_questions.json` — offline question bank (fallback)

## 5. Running the tests

```bash
# inside the container:
python -m pytest tests -q            # 39 offline tests
```

Groups: `tests/test_unit_taxonomy_metrics.py` (unit),
`tests/test_integration_pipeline.py` (pipeline with FakeLLM),
`tests/test_edge_cases.py`, `tests/test_bias_guardrails.py` (Section H/L).

## 6. Contact points for Member 2 questions

- Entry point: `agent/pipeline.py::run_agent`
- Request/output schemas: `agent/schemas.py`
- Config: `agent/config.py`
- Logging hooks (already wired): `agent/logging.py`
