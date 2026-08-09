"""Persona orchestration + bridge phrases (Section I, Section H).

* :class:`PersonaManager` — picks the next persona with the anti-dominance
  rule (no persona > 50% of turns) and tracks usage for the fairness audit.
* :func:`bridge_phrase_hint` — deterministic glue the pipeline can inject
  when the persona switches (the LLM also receives the bridge-phrase
  instruction embedded in each persona prompt, F3).
* :func:`fairness_check` — 70/30 completed-vs-skipped day targeting check.
"""
from __future__ import annotations

from collections import Counter

from agent.config import settings
from agent.schemas import Persona

_PERSONAS: tuple[Persona, ...] = (
    Persona.HIRING_MANAGER,
    Persona.SENIOR_ENGINEER,
    Persona.STAFF_ENGINEER,
)


def bridge_phrase_hint(prev_persona: Persona, next_persona: Persona) -> str | None:
    """Return a deterministic transition phrase for a persona switch."""
    if prev_persona is None or prev_persona == next_persona:
        return None
    hints = {
        (Persona.SENIOR_ENGINEER, Persona.HIRING_MANAGER): "let's zoom out to the business side",
        (Persona.HIRING_MANAGER, Persona.SENIOR_ENGINEER): "let me dig into the technical details",
        (Persona.SENIOR_ENGINEER, Persona.STAFF_ENGINEER): "now let's think about scale",
        (Persona.STAFF_ENGINEER, Persona.SENIOR_ENGINEER): "let's focus on the implementation",
        (Persona.HIRING_MANAGER, Persona.STAFF_ENGINEER): "let's take an architect's view",
        (Persona.STAFF_ENGINEER, Persona.HIRING_MANAGER): "let's zoom back out to impact",
    }
    return hints.get((prev_persona, next_persona))


class PersonaManager:
    """Tracks persona usage and selects the next balanced persona."""

    def __init__(
        self,
        usage: Counter | dict | None = None,
        current: Persona | None = None,
        total_turns: int = 0,
    ) -> None:
        if isinstance(usage, Counter):
            self.usage: Counter[str] = Counter(usage)
        elif isinstance(usage, dict):
            self.usage = Counter({k: v for k, v in usage.items() if v > 0})
        else:
            self.usage = Counter()
        self.total_turns = total_turns or sum(self.usage.values())
        self.current = current

    def record(self, persona: Persona) -> None:
        """Record that a turn was conducted under *persona*."""
        self.usage[persona.value] += 1
        self.total_turns += 1
        self.current = persona

    def next_persona(self) -> Persona:
        """Pick the persona for the coming turn.

        Opens as ``senior_engineer``; thereafter prefers unused personas
        (fresh coverage), then the least-used; round-robin tie-break.
        No persona can dominate past the 50% cap (Section H).
        """
        if self.total_turns == 0:
            return Persona.SENIOR_ENGINEER
        unused = [p for p in _PERSONAS if self.usage[p.value] == 0]
        if unused:
            return unused[0]
        return min(_PERSONAS, key=lambda p: (self.usage[p.value], p.value))

    def dominance_violated(self) -> bool:
        """True if any persona exceeds ``persona_dominance_cap`` of turns."""
        if self.total_turns < 2:
            return False
        return any(
            self.usage[p.value] / self.total_turns > settings.persona_dominance_cap
            for p in _PERSONAS
        )

    def distribution(self) -> dict[str, float]:
        """Persona -> fraction of turns (for the bias audit log)."""
        if not self.total_turns:
            return {}
        return {p.value: self.usage[p.value] / self.total_turns for p in _PERSONAS}


def fairness_check(completed_count: int, skipped_count: int) -> tuple[bool, str]:
    """Enforce the ~70/30 completed-vs-skipped question targeting (Section H).

    Returns (ok, reason).  ok=False signals the caller should re-balance
    its day selection (e.g., prefer completed days).
    """
    total = completed_count + skipped_count
    if total == 0:
        return True, "no day targets"
    ratio = completed_count / total
    ok = ratio >= settings.completed_day_target_ratio
    return ok, (
        f"completed ratio {ratio:.1%} vs target "
        f"{settings.completed_day_target_ratio:.1%} {'OK' if ok else 'OFF'}"
    )