"""Smoke test for F10 persona orchestration."""
from collections import Counter

from agent.persona import PersonaManager, bridge_phrase_hint, fairness_check
from agent.schemas import Persona

# 1. Fresh manager starts with senior_engineer
m = PersonaManager()
assert m.next_persona() == Persona.SENIOR_ENGINEER
print("1. First persona:", m.next_persona().value)

# 2. Unused personas get priority
m.record(Persona.SENIOR_ENGINEER)
m.record(Persona.SENIOR_ENGINEER)
m.record(Persona.SENIOR_ENGINEER)
assert m.next_persona() in (Persona.HIRING_MANAGER, Persona.STAFF_ENGINEER)
print("2. Unused personas prioritized after senior_engineer dominates")

# 3. Anti-dominance: 4 senior turns of 6 would violate the 50% cap
m2 = PersonaManager(Counter({"senior_engineer": 4}), total_turns=6)
assert m2.usage["senior_engineer"] / 6 > 0.5
assert m2.dominance_violated()
print("3. Dominance detection:", m2.distribution(), "-> violated:", m2.dominance_violated())

# 4. Balanced distribution is not a violation
m3 = PersonaManager(Counter({"senior_engineer": 2, "hiring_manager": 2, "staff_engineer": 2}), total_turns=6)
assert not m3.dominance_violated()
print("4. Balanced -> violation False")

# 5. Bridge phrases for known transitions
b1 = bridge_phrase_hint(Persona.SENIOR_ENGINEER, Persona.HIRING_MANAGER)
assert b1 and "business" in b1
b2 = bridge_phrase_hint(Persona.HIRING_MANAGER, Persona.STAFF_ENGINEER)
assert b2 and "architect" in b2
b3 = bridge_phrase_hint(Persona.SENIOR_ENGINEER, Persona.SENIOR_ENGINEER)
assert b3 is None
print("5. Bridge hints:", b1, "|", b2, "| same-persona:", b3)

# 6. Fairness check: mostly-completed ok, mostly-skipped off
ok, reason = fairness_check(3, 1)
assert ok, reason
print("6. Fairness 75/25:", ok, reason)
bad, reason_bad = fairness_check(1, 5)
assert not bad
print("   Fairness 17/83:", bad, reason_bad)

print("\nF10 persona smoke tests passed.")