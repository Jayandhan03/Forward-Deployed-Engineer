"""Handoff vs delegation.

Handoff:    control TRANSFERS. The new agent takes over the conversation (triage -> billing).
Delegation: control stays with the caller. A sub-agent does a bounded job and returns a result.

The thing that breaks in real systems is what gets passed along, so both use an explicit
context object instead of "just the whole chat history".

Run:
    python handoffs.py
"""

from dataclasses import dataclass, field


@dataclass
class Context:
    """What crosses an agent boundary. Small, explicit, and inspectable."""
    user: str
    goal: str
    facts: dict = field(default_factory=dict)
    trail: list[str] = field(default_factory=list)       # who handled it, for debugging/audit


# --- Handoff: each agent returns the NEXT agent's name (or None when finished) ---------------

def triage(ctx: Context) -> str | None:
    ctx.trail.append("triage")
    ctx.facts["category"] = "billing" if "invoice" in ctx.goal else "tech"
    return ctx.facts["category"]                          # hand off


def billing(ctx: Context) -> str | None:
    ctx.trail.append("billing")
    ctx.facts["answer"] = "INV-7 was charged twice; refund started"
    return None                                           # finished, billing owns the reply


def tech(ctx: Context) -> str | None:
    ctx.trail.append("tech")
    ctx.facts["answer"] = "Try clearing the cache"
    return None


AGENTS = {"triage": triage, "billing": billing, "tech": tech}


def run_with_handoffs(ctx: Context, start="triage", max_hops=4) -> Context:
    current = start
    for _ in range(max_hops):                             # cap hops: agents can ping-pong forever
        nxt = AGENTS[current](ctx)
        if nxt is None:
            return ctx
        current = nxt
    ctx.facts["answer"] = "too many handoffs, escalating to a human"
    return ctx


# --- Delegation: the caller keeps control and uses the sub-agent's return value --------------

def delegate_summary(text: str) -> str:
    """A sub-agent with its OWN fresh context: it never sees the parent's history."""
    return text[:30] + "..."


def orchestrator(ctx: Context) -> str:
    ctx.trail.append("orchestrator")
    summary = delegate_summary("A very long ticket thread about duplicate charges on invoice 7 ...")
    ctx.trail.append("summariser(delegated)")
    return f"Reply drafted by orchestrator using summary: {summary!r}"


if __name__ == "__main__":
    ctx = run_with_handoffs(Context("alice", "I was charged twice on my invoice"))
    print("HANDOFF")
    print("  trail:", " -> ".join(ctx.trail))
    print("  answer:", ctx.facts["answer"])

    ctx2 = Context("alice", "draft a reply")
    print("\nDELEGATION")
    print("  result:", orchestrator(ctx2))
    print("  trail:", " -> ".join(ctx2.trail), " (orchestrator stayed in charge)")
