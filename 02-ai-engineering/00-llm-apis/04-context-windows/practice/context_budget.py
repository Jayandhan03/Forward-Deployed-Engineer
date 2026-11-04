"""Context windows: count tokens against the limit, and decide what to cut before you hit it.

Tokens are approximated as chars / 4 (rough for English). For exact counts use the provider's
token-counting endpoint; the budgeting logic below stays the same.

Run:
    python context_budget.py
"""

CONTEXT_LIMIT = 8_000
RESERVED_FOR_OUTPUT = 1_500          # the reply also has to fit in the window


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def plan(parts: list[tuple[str, str, int]]) -> None:
    """parts = (name, text, priority). Lower priority number = more important = cut last."""
    available = CONTEXT_LIMIT - RESERVED_FOR_OUTPUT
    total = sum(approx_tokens(t) for _, t, _ in parts)
    print(f"limit {CONTEXT_LIMIT}, output reserve {RESERVED_FOR_OUTPUT} -> {available} tokens for input")
    print(f"input is ~{total} tokens ({total / available:.0%} of what's available)\n")

    kept, used, dropped = [], 0, []
    for name, text, _ in sorted(parts, key=lambda p: p[2]):
        cost = approx_tokens(text)
        if used + cost <= available:
            kept.append((name, cost))
            used += cost
        else:
            dropped.append((name, cost))

    for name, cost in kept:
        print(f"  keep  {name:<22} {cost:>6} tokens")
    for name, cost in dropped:
        print(f"  DROP  {name:<22} {cost:>6} tokens  <- over budget")
    print(f"\nfinal input ~{used} tokens, headroom {available - used}")


if __name__ == "__main__":
    plan([
        ("system prompt", "You are a support agent. " * 40, 0),
        ("user question", "Why was I charged twice? " * 10, 0),
        ("retrieved doc A", "Refund policy details. " * 400, 1),
        ("retrieved doc B", "Billing FAQ entry. " * 600, 2),
        ("old chat history", "Earlier we talked about shipping. " * 900, 3),
    ])
    print("\nLong context is not free: cost and latency grow with input size, and models attend less")
    print("reliably to the middle of very long prompts. Budget it; don't just fill it.")
