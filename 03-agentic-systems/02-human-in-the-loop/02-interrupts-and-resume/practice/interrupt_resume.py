"""Durable pause and resume: checkpoint run state to disk, stop, resume later (even in a new process).

The workflow is a list of steps; one step needs human input and pauses the run.

Run:
    python interrupt_resume.py
"""

import json
import tempfile
from pathlib import Path

CHECKPOINT = Path(tempfile.gettempdir()) / "agent_run_demo.json"

STEPS = ["gather_facts", "draft_refund", "WAIT_FOR_APPROVAL", "issue_refund", "notify_customer"]


def save(state: dict) -> None:
    CHECKPOINT.write_text(json.dumps(state, indent=2))


def load() -> dict:
    return json.loads(CHECKPOINT.read_text())


def run(state: dict, human_input: str | None = None) -> dict:
    """Advance from state['next_step']. Safe to call again after a crash: finished steps are skipped."""
    while state["next_step"] < len(STEPS):
        step = STEPS[state["next_step"]]
        if step == "WAIT_FOR_APPROVAL":
            if human_input is None:
                state["status"] = "paused"
                save(state)
                print(f"  paused at step {state['next_step']}, waiting for approval")
                return state
            state["log"].append(f"human said: {human_input}")
            if human_input != "approve":
                state["status"] = "rejected"
                save(state)
                return state
        else:
            state["log"].append(f"did {step}")
        state["next_step"] += 1
        state["status"] = "running"
        save(state)                      # checkpoint after EVERY step
    state["status"] = "done"
    save(state)
    return state


if __name__ == "__main__":
    print("process 1: start run")
    run({"run_id": "r-1", "next_step": 0, "status": "new", "log": []})

    print("...process 1 exits; nothing in memory...\n")

    print("process 2: human approves, resume from the checkpoint")
    final = run(load(), human_input="approve")
    print(f"  status={final['status']}")
    for line in final["log"]:
        print("   -", line)
    CHECKPOINT.unlink()
