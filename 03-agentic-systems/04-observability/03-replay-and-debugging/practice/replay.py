"""Replay a run from its recorded trace: re-run the agent with recorded model outputs and tool
results instead of calling anything live. Deterministic, free, and safe (no real side effects).

Run:
    python replay.py
"""

# A recorded run: what the model said and what each tool returned.
TRACE = [
    {"type": "model", "output": {"tool": "lookup_order", "args": {"id": 881}}},
    {"type": "tool", "name": "lookup_order", "result": {"amount": 42, "status": "paid"}},
    {"type": "model", "output": {"tool": "refund_order", "args": {"id": 881, "amount": 420}}},   # bug here
    {"type": "tool", "name": "refund_order", "result": {"ok": True}},
    {"type": "model", "output": {"text": "Refunded."}},
]


class Replayer:
    """Hands back recorded outputs in order. Fails loudly if the agent diverges from the trace."""

    def __init__(self, trace):
        self.steps = iter(trace)

    def model(self):
        step = next(self.steps)
        assert step["type"] == "model", f"expected a model step, trace has {step['type']}"
        return step["output"]

    def tool(self, name, args):
        step = next(self.steps)
        assert step["type"] == "tool" and step["name"] == name, \
            f"agent called {name} but trace recorded {step.get('name')}"
        return step["result"]


def agent(llm, call_tool, on_step):
    """The agent loop. The same code runs live (real model/tools) or in replay."""
    lookup = None
    while True:
        out = llm()
        on_step(out)
        if "text" in out:
            return out["text"]
        result = call_tool(out["tool"], out["args"])
        if out["tool"] == "lookup_order":
            lookup = result
        if out["tool"] == "refund_order" and lookup and out["args"]["amount"] > lookup["amount"]:
            print(f"  !! refund {out['args']['amount']} exceeds order total {lookup['amount']}")


if __name__ == "__main__":
    r = Replayer(TRACE)
    print("replaying recorded run, step by step:")
    steps = []
    answer = agent(r.model, r.tool, lambda s: (steps.append(s), print("  step", len(steps), s)))
    print("final:", answer)
    print("\nThe bug is visible without touching the payments API: the model asked to refund 420 on a $42 order.")
