"""The Thread Puller — AI Agent layer.

Owns: prompt engineering, context management, output validation,
persona orchestration, and feedback synthesis.

Public entrypoint: ``agent.pipeline.run_agent`` (async).
"""
from agent.config import settings

__version__ = "0.1.0"

__all__ = ["__version__", "settings"]
