"""Prompt versioning and regression testing: prompts are code. Version them, test them, compare them.

A tiny registry keyed by content hash, a stand-in model, and a test that scores each version on the
same cases so you can see whether a "small tweak" helped or broke something.

Run:
    python prompt_registry.py
"""

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVersion:
    name: str
    version: int
    template: str

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.template.encode()).hexdigest()[:8]     # same text = same id

    def render(self, **vars) -> str:
        return self.template.format(**vars)


REGISTRY: dict[str, list[PromptVersion]] = {}


def register(name: str, template: str) -> PromptVersion:
    versions = REGISTRY.setdefault(name, [])
    if versions and versions[-1].template == template:
        return versions[-1]                                              # unchanged, no new version
    pv = PromptVersion(name, len(versions) + 1, template)
    versions.append(pv)
    return pv


def fake_model(prompt: str) -> str:
    """Stand-in whose behaviour depends on the prompt wording, like a real model does."""
    q = prompt.split("Question:")[-1].lower()
    if "json" in prompt.lower():
        return '{"category": "billing"}' if "charge" in q else '{"category": "other"}'
    return "Billing question." if "charge" in q else "Something else."


CASES = [
    ("Why was I charged twice?", '"billing"'),
    ("My app keeps crashing", '"other"'),
    ("Refund the extra charge", '"billing"'),
]


def evaluate(pv: PromptVersion) -> float:
    passed = sum(expected in fake_model(pv.render(question=q)) for q, expected in CASES)
    return passed / len(CASES)


if __name__ == "__main__":
    v1 = register("classify", "Classify the ticket.\nQuestion: {question}")
    v2 = register("classify", "Classify the ticket. Reply with JSON like {{\"category\": \"...\"}}.\nQuestion: {question}")
    again = register("classify", v2.template)                            # re-registering identical text

    print(f"registered versions: {[(v.version, v.digest) for v in REGISTRY['classify']]}")
    print(f"re-registering identical text made a new version? {again is not v2}\n")

    scores = {v.version: evaluate(v) for v in REGISTRY["classify"]}
    for ver, score in scores.items():
        print(f"v{ver}: pass rate {score:.0%}")

    best = max(scores, key=scores.get)
    print(f"\nShip v{best}. Log the digest ({REGISTRY['classify'][best - 1].digest}) with every production")
    print("call so you can always answer: which exact prompt produced this output?")
