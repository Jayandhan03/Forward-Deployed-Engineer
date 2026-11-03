"""A single-agent workflow: one loop, a small toolset, and a budget that is actually enforced.

The model is scripted so it runs offline. The point is the harness around the loop:
step limit, token budget, tool errors as data, and a clear stop reason in the result.

Run:
    python single_agent_budgeted.py
"""

from dataclasses import dataclass

TOOLS = {
    "search_docs": lambda q: f"3 docs about {q}",
    "get_price": lambda sku: {"A1": "9.99", "B2": "24.50"}[sku],      # KeyError on unknown sku
}

# What the scripted "model" does on each turn: ("tool", name, arg) or ("final", text)
SCRIPT = [
    ("tool", "search_docs", "shipping"),
    ("tool", "get_price", "ZZ"),            # bad sku -> tool error goes back to the model
    ("tool", "get_price", "A1"),            # model corrects itself
    ("final", "Shipping is free over $20; A1 costs $9.99."),
]


@dataclass
class Result:
    stop_reason: str
    answer: str | None
    steps: int
    tokens: int


def run(script, max_steps=6, token_budget=2000) -> Result:
    transcript, tokens = [], 0
    for step, turn in enumerate(script, start=1):
        if step > max_steps:
            return Result("max_steps", None, step - 1, tokens)
        tokens += 300 + 40 * len(transcript)               # context grows every turn
        if tokens > token_budget:
            return Result("token_budget", None, step - 1, tokens)

        if turn[0] == "final":
            return Result("done", turn[1], step, tokens)

        _, name, arg = turn
        try:
            observation = TOOLS[name](arg)
        except Exception as e:                              # errors are data, never a crash
            observation = f"ERROR: {type(e).__name__}: {e}"
        transcript.append((name, arg, observation))
        print(f"  step {step}: {name}({arg!r}) -> {observation}")
    return Result("script_ended", None, len(script), tokens)


if __name__ == "__main__":
    print("normal run:")
    print(" ", run(SCRIPT))
    print("\ntight step limit:")
    print(" ", run(SCRIPT, max_steps=2))
    print("\ntight token budget:")
    print(" ", run(SCRIPT, token_budget=700))
