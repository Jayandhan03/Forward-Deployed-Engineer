"""Assemble the context window each turn under a token budget.

Priority: system prompt and the current task are never dropped; then recent turns; then old turns
get summarised; tool results are truncated. Tokens are approximated as chars / 4.

Run:
    python context_assembly.py
"""


def tokens(text: str) -> int:
    return max(1, len(text) // 4)


def truncate(text: str, max_tokens: int) -> str:
    if tokens(text) <= max_tokens:
        return text
    keep = max_tokens * 4
    return text[:keep] + f" ...[truncated {len(text) - keep} chars]"


def summarise(old_turns: list[dict]) -> str:
    """Stand-in for an LLM summarisation call."""
    return f"[summary of {len(old_turns)} earlier messages: user asked about invoices, agent looked up INV-1..INV-3]"


def assemble(system: str, task: str, history: list[dict], budget: int, tool_cap: int = 60) -> list[dict]:
    fixed = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    used = sum(tokens(m["content"]) for m in fixed)

    # Cap every tool result first: they are the usual context hogs.
    history = [{**m, "content": truncate(m["content"], tool_cap)} if m["role"] == "tool" else m
               for m in history]

    kept: list[dict] = []
    for msg in reversed(history):                       # newest first
        cost = tokens(msg["content"])
        if used + cost > budget - 40:                   # leave room for a summary line
            break
        kept.insert(0, msg)
        used += cost

    dropped = history[: len(history) - len(kept)]
    middle = [{"role": "system", "content": summarise(dropped)}] if dropped else []
    return fixed[:1] + middle + kept + fixed[1:]


if __name__ == "__main__":
    history = []
    for i in range(1, 9):
        history.append({"role": "assistant", "content": f"Looking up INV-{i}"})
        history.append({"role": "tool", "content": f"INV-{i}: " + "line item " * 80})

    window = assemble("You are a billing assistant.", "Which invoice is largest?", history, budget=300)
    print(f"{len(history)} messages in history -> {len(window)} in the window")
    print(f"window ~{sum(tokens(m['content']) for m in window)} tokens (budget 300)\n")
    for m in window:
        print(f"{m['role']:<10} {m['content'][:70]!r}")
