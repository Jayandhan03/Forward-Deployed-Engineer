"""One front door for every tool call: identity -> permission -> rate limit -> run -> audit.

Run:
    python tool_gateway.py
"""

import time
from dataclasses import dataclass, field


@dataclass
class Principal:
    """Who is acting. An agent always acts for someone, with limited scopes."""
    agent_id: str
    user_id: str
    scopes: set[str]


# The tool registry: name -> (function, scope needed to call it)
def get_invoice(invoice_id: str) -> dict:
    return {"id": invoice_id, "amount": 120.0, "status": "unpaid"}


def refund_invoice(invoice_id: str) -> dict:
    return {"id": invoice_id, "status": "refunded"}


TOOLS = {
    "get_invoice": (get_invoice, "invoices:read"),
    "refund_invoice": (refund_invoice, "invoices:refund"),
}


@dataclass
class Gateway:
    max_calls_per_minute: int = 5
    audit: list[dict] = field(default_factory=list)
    _calls: dict[str, list[float]] = field(default_factory=dict)

    def call(self, who: Principal, tool: str, **args):
        decision, result = self._decide_and_run(who, tool, args)
        # Audit EVERY attempt, allowed or not. Denials are the interesting ones.
        self.audit.append({"ts": time.time(), "agent": who.agent_id, "user": who.user_id,
                           "tool": tool, "args": args, "decision": decision})
        return decision, result

    def _decide_and_run(self, who, tool, args):
        if tool not in TOOLS:
            return "deny:unknown_tool", None
        fn, needed_scope = TOOLS[tool]
        if needed_scope not in who.scopes:
            return f"deny:missing_scope:{needed_scope}", None
        recent = [t for t in self._calls.get(who.agent_id, []) if time.time() - t < 60]
        if len(recent) >= self.max_calls_per_minute:
            return "deny:rate_limited", None
        self._calls[who.agent_id] = recent + [time.time()]
        return "allow", fn(**args)


if __name__ == "__main__":
    gw = Gateway(max_calls_per_minute=3)
    support_bot = Principal("support-agent-v2", "alice@acme.com", {"invoices:read"})

    for tool, args in [("get_invoice", {"invoice_id": "INV-1"}),
                       ("refund_invoice", {"invoice_id": "INV-1"}),   # no scope
                       ("delete_database", {}),                       # not registered
                       ("get_invoice", {"invoice_id": "INV-2"}),
                       ("get_invoice", {"invoice_id": "INV-3"}),
                       ("get_invoice", {"invoice_id": "INV-4"})]:     # over the rate limit
        decision, _ = gw.call(support_bot, tool, **args)
        print(f"{tool:<16} -> {decision}")

    print(f"\n{len(gw.audit)} audit events recorded (allowed and denied).")
