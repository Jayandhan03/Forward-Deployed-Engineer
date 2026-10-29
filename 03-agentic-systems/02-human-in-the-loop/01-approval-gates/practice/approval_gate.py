"""Approval gate: the agent proposes, a human disposes, for risky tools only.

The "model" is a scripted list of tool requests so this runs offline.

Run:
    python approval_gate.py
"""

from dataclasses import dataclass

RISK = {"search_orders": "low", "send_email": "high", "refund_order": "high"}


def search_orders(customer: str) -> str:
    return f"{customer} has order #881 ($42.00)"


def send_email(to: str, body: str) -> str:
    return f"email sent to {to}"


def refund_order(order_id: str, amount: float) -> str:
    return f"refunded ${amount:.2f} on {order_id}"


TOOLS = {"search_orders": search_orders, "send_email": send_email, "refund_order": refund_order}


@dataclass
class Decision:
    verdict: str            # approve | reject | edit
    edited_args: dict | None = None
    reason: str = ""


def ask_human(tool: str, args: dict) -> Decision:
    """Stand-in for a UI/Slack prompt. Replace with a real queue in production (see review-queues)."""
    if tool == "refund_order":
        return Decision("edit", {"order_id": args["order_id"], "amount": 20.0}, "partial refund only")
    return Decision("approve")


def run(plan: list[tuple[str, dict]]) -> None:
    audit = []
    for tool, args in plan:
        if RISK[tool] == "high":
            d = ask_human(tool, args)
            audit.append({"tool": tool, "asked": True, "verdict": d.verdict, "reason": d.reason})
            if d.verdict == "reject":
                print(f"{tool}: REJECTED -> tell the model: '{d.reason}'")
                continue
            if d.verdict == "edit":
                print(f"{tool}: human edited args {args} -> {d.edited_args}")
                args = d.edited_args
        else:
            audit.append({"tool": tool, "asked": False, "verdict": "auto"})
        print(f"{tool}: {TOOLS[tool](**args)}")
    print("\naudit:", audit)


if __name__ == "__main__":
    run([
        ("search_orders", {"customer": "alice"}),                         # low risk: runs unprompted
        ("send_email", {"to": "alice@example.com", "body": "Sorry!"}),    # high: approved as-is
        ("refund_order", {"order_id": "881", "amount": 42.0}),            # high: human edits amount
    ])
