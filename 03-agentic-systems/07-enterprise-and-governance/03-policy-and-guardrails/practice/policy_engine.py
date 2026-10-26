"""Policy as code: rules live outside the prompt, default is deny, risky things need a human.

Run:
    python policy_engine.py
"""

import re
from dataclasses import dataclass

# Rules are data, so security/compliance can review and change them without touching agent code.
# First match wins. The last rule is the default.
RULES = [
    {"if": {"risk": "read"},                     "then": "allow"},
    {"if": {"risk": "write", "tainted": True},   "then": "approve"},
    {"if": {"risk": "write", "env": "prod"},     "then": "approve"},
    {"if": {"risk": "write"},                    "then": "allow"},
    {"if": {"risk": "irreversible"},             "then": "approve"},
    {"if": {},                                   "then": "deny"},
]


@dataclass
class Action:
    tool: str
    risk: str               # read | write | irreversible
    env: str = "dev"
    tainted: bool = False   # did untrusted content (web page, email, upload) enter the context?


def decide(action: Action) -> str:
    facts = vars(action)
    for rule in RULES:
        if all(facts.get(k) == v for k, v in rule["if"].items()):
            return rule["then"]
    return "deny"


PII = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "phone": re.compile(r"\+?\d[\d ()-]{8,}\d"),
}


def redact(text: str) -> str:
    """Strip PII before it goes to a model, a log line, or a third party."""
    for name, pattern in PII.items():
        text = pattern.sub(f"[{name.upper()}]", text)
    return text


if __name__ == "__main__":
    cases = [
        Action("search_docs", "read"),
        Action("update_ticket", "write", env="dev"),
        Action("update_ticket", "write", env="prod"),
        Action("update_ticket", "write", env="dev", tainted=True),   # prompt-injection safety net
        Action("delete_account", "irreversible"),
        Action("mystery_tool", "unknown"),
    ]
    for a in cases:
        extra = " (untrusted content in context)" if a.tainted else ""
        print(f"{a.tool:<15} risk={a.risk:<12} env={a.env:<5} -> {decide(a)}{extra}")

    print()
    print(redact("Contact bob@corp.com or +1 415 555 0134, card 4111 1111 1111 1111"))
