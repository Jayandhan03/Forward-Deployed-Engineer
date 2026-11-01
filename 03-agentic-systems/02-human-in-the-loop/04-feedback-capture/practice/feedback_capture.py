"""Feedback capture: store thumbs/edits against the run, then turn corrections into eval cases.

Run:
    python feedback_capture.py
"""

import json
from dataclasses import asdict, dataclass


@dataclass
class Feedback:
    run_id: str
    task: str
    agent_answer: str
    kind: str                       # thumbs_up | thumbs_down | edit
    corrected_answer: str | None = None
    comment: str = ""


STORE: list[Feedback] = []


def capture(**kw) -> None:
    STORE.append(Feedback(**kw))


def to_eval_cases(feedback: list[Feedback]) -> list[dict]:
    """An edit is gold: the human told you the right answer. Thumbs-down without an edit is a
    candidate to review, not yet a test."""
    cases = []
    for f in feedback:
        if f.kind == "edit" and f.corrected_answer:
            cases.append({"name": f"from_run_{f.run_id}", "task": f.task,
                          "expected": f.corrected_answer, "was": f.agent_answer})
    return cases


if __name__ == "__main__":
    capture(run_id="r1", task="Summarise ticket 41", agent_answer="Login bug", kind="thumbs_up")
    capture(run_id="r2", task="What is the refund window?", agent_answer="14 days",
            kind="edit", corrected_answer="30 days", comment="policy changed in March")
    capture(run_id="r3", task="Who owns billing?", agent_answer="Sam", kind="thumbs_down")

    up = sum(f.kind == "thumbs_up" for f in STORE)
    print(f"{len(STORE)} feedback items, {up} positive")
    print("\nneeds triage (thumbs down, no edit):",
          [f.run_id for f in STORE if f.kind == "thumbs_down" and not f.corrected_answer])

    print("\nnew eval cases from edits:")
    print(json.dumps(to_eval_cases(STORE), indent=2))
