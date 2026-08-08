"""Smoke test for F6 LLM client — JSON extraction + cosine similarity.

Offline-only: does not hit the network.  Mock the chat path instead.
"""
import asyncio

from agent.llm_client import _extract_json, cosine_similarity

# 1. Direct JSON parse
assert _extract_json('{"a": 1}') == {"a": 1}
print("1. Direct parse OK")

# 2. Fenced JSON block
raw = 'Sure! Here you go:\n```json\n{"question": "Why?", "type": "challenge"}\n```'
parsed = _extract_json(raw)
assert parsed and parsed["question"] == "Why?"
print("2. Fenced block OK")

# 3. Braced block in prose
raw2 = 'The answer is {"score": 7, "note": "ok"} thanks'
parsed2 = _extract_json(raw2)
assert parsed2 and parsed2["score"] == 7
print("3. Braced-block extraction OK")

# 4. Non-JSON → None
assert _extract_json("not json at all") is None
print("4. Invalid input -> None OK")

# 5. Cosine similarity
a = [1.0, 0.0]
b = [1.0, 0.0]
c = [0.0, 1.0]
assert abs(cosine_similarity(a, b) - 1.0) < 1e-9
assert abs(cosine_similarity(a, c)) < 1e-9
assert cosine_similarity([], [1.0]) == 0.0
print("5. Cosine similarity OK:", round(cosine_similarity(a, b), 3))

print("\nF6 offline smoke tests passed (network calls mocked in F15 tests).")