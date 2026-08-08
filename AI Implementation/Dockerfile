# ── build stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build deps for numpy / chromadb wheels on slim.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ── runtime stage ────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_DIR=/tmp/interview_logs

WORKDIR /app

# Copy installed packages from builder.
COPY --from=builder /install /usr/local

# Create non-root user for safety.
RUN groupadd -r threadpuller && \
    useradd -r -g threadpuller -d /app threadpuller && \
    mkdir -p /app/data /tmp/interview_logs && \
    chown -R threadpuller:threadpuller /app /tmp/interview_logs

# Copy application source.
COPY --chown=threadpuller:threadpuller agent/ ./agent/
COPY --chown=threadpuller:threadpuller scripts/ ./scripts/
COPY --chown=threadpuller:threadpuller tests/ ./tests/
COPY --chown=threadpuller:threadpuller docs/ ./docs/

# Seed data files (overridden by compose volume mounts at runtime).
COPY --chown=threadpuller:threadpuller data/ ./data/

USER threadpuller

# Flexible entrypoint: defaults to the offline interview demo.
# Override with: docker run threadpuller-agent pytest tests/
#                docker run threadpuller-agent python scripts/poc/poc1_static_prompt.py
#                docker compose run --rm agent pytest tests/
ENTRYPOINT ["python"]
CMD ["/app/scripts/poc/poc2_offline_interview.py"]
