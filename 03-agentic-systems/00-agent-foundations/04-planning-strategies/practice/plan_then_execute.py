"""Planning: ReAct (decide one step at a time) vs plan-then-execute (decide up front, then run).

Both solve the same task with scripted "decisions" so the difference in LLM calls is visible.
Plan-then-execute also shows re-planning when a step fails.

Run:
    python plan_then_execute.py
"""

TASK = "Find the largest overdue invoice and email its owner"

TOOLS = {
    "list_overdue": lambda: [{"id": "INV-3", "amt": 90, "owner": "sam"}, {"id": "INV-7", "amt": 400, "owner": "ana"}],
    "largest": lambda invoices: max(invoices, key=lambda i: i["amt"]),
    "send_email": lambda to: f"emailed {to}",
}

llm_calls = 0


def llm(label: str) -> None:
    """Every call here stands for one (slow, paid) model call."""
    global llm_calls
    llm_calls += 1
    print(f"   [llm call {llm_calls}] {label}")


def react() -> str:
    """Think -> act -> observe, one step per model call. Flexible, but a call per step."""
    llm("what next? -> list_overdue")
    invoices = TOOLS["list_overdue"]()
    llm("saw 2 invoices; what next? -> largest")
    top = TOOLS["largest"](invoices)
    llm(f"largest is {top['id']}; what next? -> send_email")
    out = TOOLS["send_email"](top["owner"])
    llm("done? -> final answer")
    return out


def plan_then_execute(broken_tool: str | None = None) -> str:
    """One call writes the whole plan; code runs it. Cheaper, but must handle plans going stale."""
    llm("write the full plan")
    plan = ["list_overdue", "largest", "send_email"]
    data, replanned = None, False
    while plan:
        step = plan[0]
        try:
            if step == broken_tool:
                raise RuntimeError(f"{step} is unavailable")
            data = (TOOLS[step]() if step == "list_overdue"
                    else TOOLS[step](data) if step == "largest"
                    else TOOLS[step](data["owner"]))
            plan.pop(0)
        except RuntimeError as e:
            if replanned:
                raise                                   # don't re-plan forever
            replanned = True
            llm(f"step failed ({e}) -> re-plan the remaining steps")
            # The revised plan routes around the broken step (here: pick the max by hand).
            data = max(data, key=lambda i: i["amt"])
            plan = ["send_email"]
    return data


if __name__ == "__main__":
    for name, fn in [("ReAct", react), ("Plan-then-execute", plan_then_execute),
                     ("Plan-then-execute with one failure", lambda: plan_then_execute(broken_tool="largest"))]:
        llm_calls = 0
        print(f"{name}:")
        print(f"   result: {fn()}  | total llm calls: {llm_calls}\n")
    print("Rule of thumb: ReAct when the path depends on what you find; plan first when the steps are known.")
