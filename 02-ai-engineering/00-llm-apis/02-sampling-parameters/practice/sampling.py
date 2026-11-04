"""Sampling parameters, from scratch: temperature, top-k, top-p on a toy next-token distribution.

A model outputs a score (logit) per token. Sampling settings reshape those scores before one token is
drawn. No API needed: this is the math behind the temperature / top_p knobs.

Run:
    python sampling.py
"""

import math
import random

LOGITS = {"the": 3.0, "a": 2.4, "this": 1.8, "banana": 0.3, "quantum": -0.5, "zebra": -1.5}


def softmax(logits: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    """Temperature divides the logits: <1 sharpens (more deterministic), >1 flattens (more random)."""
    scaled = {t: v / temperature for t, v in logits.items()}
    m = max(scaled.values())                                   # subtract max for numeric stability
    exps = {t: math.exp(v - m) for t, v in scaled.items()}
    total = sum(exps.values())
    return {t: e / total for t, e in exps.items()}


def top_k(probs: dict[str, float], k: int) -> dict[str, float]:
    kept = dict(sorted(probs.items(), key=lambda p: -p[1])[:k])
    total = sum(kept.values())
    return {t: p / total for t, p in kept.items()}


def top_p(probs: dict[str, float], p: float) -> dict[str, float]:
    """Nucleus sampling: keep the smallest set of tokens whose probability adds up to p."""
    kept, running = {}, 0.0
    for t, pr in sorted(probs.items(), key=lambda x: -x[1]):
        kept[t] = pr
        running += pr
        if running >= p:
            break
    total = sum(kept.values())
    return {t: pr / total for t, pr in kept.items()}


def show(label: str, probs: dict[str, float]) -> None:
    row = "  ".join(f"{t}={p:.2f}" for t, p in sorted(probs.items(), key=lambda x: -x[1]))
    print(f"{label:<16} {row}")


def sample(probs: dict[str, float], n: int = 1000, seed: int = 0) -> dict[str, int]:
    rng = random.Random(seed)
    draws = rng.choices(list(probs), weights=probs.values(), k=n)
    return {t: draws.count(t) for t in probs}


if __name__ == "__main__":
    for temp in (0.2, 1.0, 2.0):
        show(f"temperature={temp}", softmax(LOGITS, temp))

    base = softmax(LOGITS)
    print()
    show("top_k=3", top_k(base, 3))
    show("top_p=0.9", top_p(base, 0.9))

    print("\n1000 draws at temperature 0.2 vs 2.0:")
    print("  0.2 ->", sample(softmax(LOGITS, 0.2)))
    print("  2.0 ->", sample(softmax(LOGITS, 2.0)))
    print("\nTemperature 0 is 'always pick the top token' (greedy). Use low for extraction/tools, higher for creative text.")
    print("Change temperature OR top_p, not both: they overlap.")
