"""Validate model output before acting on it: parse, check schema and business rules, retry with the
error message, then fall back. Never trust model output just because it looks like JSON.

The "model" is scripted to be wrong in realistic ways, then right.

Run:
    python output_guardrails.py
"""

import json

ALLOWED_ACTIONS = {"refund", "escalate", "reply"}
MAX_REFUND = 100.0

# What the model returns on successive attempts for the same request.
SCRIPT = iter([
    "Sure! Here you go: {action: refund}",                                   # not JSON
    '{"action": "delete_everything", "amount": 5}',                          # action not allowed
    '{"action": "refund", "amount": 5000}',                                  # breaks business rule
    '{"action": "refund", "amount": 25.5, "reason": "duplicate charge"}',    # valid
])


def fake_model(prompt: str) -> str:
    return next(SCRIPT)


def validate(raw: str) -> tuple[dict | None, str | None]:
    """Return (parsed, None) if fine, else (None, message the model can act on)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"Not valid JSON ({e.msg}). Reply with a JSON object only."
    if not isinstance(data, dict):
        return None, "Top level must be a JSON object."
    if data.get("action") not in ALLOWED_ACTIONS:
        return None, f"'action' must be one of {sorted(ALLOWED_ACTIONS)}, got {data.get('action')!r}."
    if data["action"] == "refund":
        amount = data.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            return None, "'amount' must be a positive number."
        if amount > MAX_REFUND:
            return None, f"Refunds above ${MAX_REFUND:.0f} need human approval; use action 'escalate'."
        if not data.get("reason"):
            return None, "'reason' is required for refunds."
    return data, None


def get_valid_action(request: str, max_attempts: int = 4) -> dict:
    prompt = request
    for attempt in range(1, max_attempts + 1):
        raw = fake_model(prompt)
        data, error = validate(raw)
        if data:
            print(f"   attempt {attempt}: OK")
            return data
        print(f"   attempt {attempt}: rejected -> {error}")
        prompt = f"{request}\nYour last answer was rejected: {error}"      # feed the error back
    return {"action": "escalate", "reason": "model could not produce a valid action"}   # safe fallback


if __name__ == "__main__":
    print("final action:", get_valid_action("Customer says they were charged twice for $25.50"))
