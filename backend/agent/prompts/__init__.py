"""Jinja2 environment + helpers for the prompt library (Section I).

All templates live in ``agent/prompts/`` as .j2 files so prompts can be
edited without touching Python code.  Loader exposes:

    * ``render_system(persona_key, **context)``
    * ``render_user(template_name, **context)``
    * ``render(template_name, **context)``
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATE_DIR = Path(__file__).resolve().parent

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    undefined=StrictUndefined,
    autoescape=select_autoescape(enabled_extensions=(), default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)

_SYSTEM_TEMPLATES = {
    "core": "system/core.j2",
    "hiring_manager": "system/hiring_manager.j2",
    "senior_engineer": "system/senior_engineer.j2",
    "staff_engineer": "system/staff_engineer.j2",
}


def render(template_name: str, **context) -> str:
    """Render a template by relative name, e.g. 'user/question_generation.j2'."""
    return env.get_template(template_name).render(**context)


def render_system(persona_key: str, **context) -> str:
    """Render a system prompt for *persona_key* (core/hiring_manager/...)."""
    template = _SYSTEM_TEMPLATES[persona_key]
    return render(template, **context)


def render_user(template_name: str, **context) -> str:
    """Render a user prompt, e.g. render_user("question_generation", ...)."""
    return render(f"user/{template_name}.j2", **context)