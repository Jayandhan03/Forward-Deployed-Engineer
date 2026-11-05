"""Few-shot examples: choose the RIGHT examples per query, keep them balanced, and format consistently.

Static examples are fine to start. Dynamic selection (examples most similar to the query) usually
wins as the label space grows. Similarity here is word overlap so it runs offline; use embeddings
in production.

Run:
    python few_shot.py
"""

import re
from collections import Counter

EXAMPLES = [
    ("I was charged twice this month", "billing"),
    ("Refund my last payment", "billing"),
    ("The invoice total looks wrong", "billing"),
    ("App crashes when I upload a file", "technical"),
    ("Error 500 on the dashboard", "technical"),
    ("I can't log in after the update", "technical"),
    ("How do I change my email address?", "account"),
    ("Please delete my account", "account"),
]


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def select_similar(query: str, k: int = 3) -> list[tuple[str, str]]:
    q = words(query)
    scored = sorted(EXAMPLES, key=lambda e: -len(q & words(e[0])) / len(q | words(e[0])))
    return scored[:k]


def select_balanced(per_label: int = 1) -> list[tuple[str, str]]:
    """Static set with one example per label, avoiding majority-label bias."""
    seen, out = Counter(), []
    for text, label in EXAMPLES:
        if seen[label] < per_label:
            out.append((text, label))
            seen[label] += 1
    return out


def render(examples: list[tuple[str, str]], query: str) -> str:
    shots = "\n\n".join(f"Message: {t}\nCategory: {l}" for t, l in examples)
    return f"Classify each message as billing, technical or account.\n\n{shots}\n\nMessage: {query}\nCategory:"


if __name__ == "__main__":
    query = "Why does the invoice show a double charge?"

    print("STATIC, balanced (one per label):")
    print(" ", [l for _, l in select_balanced()])

    print("\nDYNAMIC, most similar to the query:")
    for text, label in select_similar(query):
        print(f"  [{label}] {text}")

    print("\nFINAL PROMPT (dynamic):\n")
    print(render(select_similar(query), query))

    print("\nTips: 3-8 examples is usually plenty; keep the format identical across shots; include a hard")
    print("or edge case; if examples are all one label the model drifts toward it; test with and without.")
