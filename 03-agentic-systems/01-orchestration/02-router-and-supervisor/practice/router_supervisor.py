"""Router vs supervisor.

Router: classify the request once, hand it to ONE specialist, done.
Supervisor: split a request into sub-tasks, dispatch to specialists, aggregate their results.

Classification is keyword-based here so it runs offline; in production it is a (cheap) model call.

Run:
    python router_supervisor.py
"""

SPECIALISTS = {
    "billing": lambda q: f"[billing] invoice looked up for: {q!r}",
    "tech": lambda q: f"[tech] troubleshooting steps for: {q!r}",
    "account": lambda q: f"[account] profile updated for: {q!r}",
}

KEYWORDS = {
    "billing": ("invoice", "refund", "charge", "payment"),
    "tech": ("error", "crash", "login", "bug"),
    "account": ("password", "email address", "profile"),
}


def classify(text: str) -> str | None:
    scores = {name: sum(k in text.lower() for k in kws) for name, kws in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def route(request: str) -> str:
    """One hop. Fast and cheap. Always have a fallback for 'no confident match'."""
    target = classify(request)
    if target is None:
        return "[fallback] I'm not sure, passing you to a human."
    return SPECIALISTS[target](request)


def supervise(request: str) -> str:
    """Split into parts, route each part, then aggregate. More power, more calls."""
    parts = [p.strip() for p in request.replace(" and ", ";").split(";") if p.strip()]
    results = [route(p) for p in parts]
    return f"{len(parts)} sub-tasks:\n  " + "\n  ".join(results)


if __name__ == "__main__":
    print("ROUTER")
    for q in ["I was charged twice on my invoice", "the app crashes on login", "what's the weather?"]:
        print(f"  {q!r}\n    -> {route(q)}")

    print("\nSUPERVISOR")
    print(" ", supervise("refund my last payment and the login page shows an error"))
