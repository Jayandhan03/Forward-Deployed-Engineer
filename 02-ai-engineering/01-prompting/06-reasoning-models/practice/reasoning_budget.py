"""Reasoning models: when extra "thinking" pays for itself, and what it costs.

Reasoning models spend hidden thinking tokens before answering. They help on multi-step problems
and add cost and latency on easy ones. Rule used here: turn thinking on only when
    (accuracy gain) x (value of a correct answer)  >  (extra cost of the thinking tokens)

All numbers are illustrative. Replace them with your provider's prices and your own measurements.

Run:
    python reasoning_budget.py
"""

PRICE_OUT_PER_MTOK = 15.00        # thinking tokens are billed as output tokens (example price)
TOKENS_PER_SECOND = 80            # rough generation speed, example

TASKS = [
    # (name, thinking_tokens_if_enabled, accuracy_without, accuracy_with, $ value of a correct answer)
    ("extract invoice number",           100, 0.99, 0.99, 0.05),
    ("classify support ticket",          800, 0.93, 0.94, 0.10),
    ("multi-step refund eligibility",   3000, 0.71, 0.92, 2.00),
    ("debug failing SQL query",         6000, 0.55, 0.85, 3.00),
]


def cost(tokens: int) -> float:
    return tokens * PRICE_OUT_PER_MTOK / 1e6


def worth_thinking(think_tokens: int, acc_off: float, acc_on: float, value: float) -> bool:
    return (acc_on - acc_off) * value > cost(think_tokens)


if __name__ == "__main__":
    print(f"{'task':<31}{'acc off':>8}{'acc on':>8}{'gain $':>8}{'cost $':>8}{'extra s':>9}  decision")
    for name, think, off, on, value in TASKS:
        gain = (on - off) * value
        print(f"{name:<31}{off:>8.0%}{on:>8.0%}{gain:>8.4f}{cost(think):>8.4f}{think / TOKENS_PER_SECOND:>9.1f}  "
              f"{'THINK' if worth_thinking(think, off, on, value) else 'skip'}")

    calls = 20_000          # per day, spread evenly over the four task types
    per_task = calls / len(TASKS)
    always = sum(cost(t) for _, t, *_ in TASKS) * per_task
    routed = sum(cost(t) for _, t, off, on, v in TASKS if worth_thinking(t, off, on, v)) * per_task
    print(f"\nthinking-token spend at {calls:,} calls/day: always-on ${always:,.2f}/day, routed ${routed:,.2f}/day")
    print("\nTips: cap the thinking budget; don't add 'think step by step' to a model that already reasons;")
    print("measure accuracy with and without on YOUR tasks before paying for it everywhere.")
