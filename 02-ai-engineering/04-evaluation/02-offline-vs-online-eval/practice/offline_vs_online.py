"""Offline vs online evaluation.

Offline: a fixed dataset, run before shipping. Repeatable, cheap, but only covers what you thought of.
Online: real traffic, measured after shipping. Honest, but noisy and needs enough volume.

This script shows both on the same two prompt variants, including the thing people forget online:
whether the difference is bigger than noise.

Run:
    python offline_vs_online.py
"""

import math
import random

random.seed(11)

# Pretend the true success rates of two variants on REAL traffic (unknown to us in real life).
TRUE_RATE = {"A (current)": 0.80, "B (candidate)": 0.84}


def offline_eval(variant: str, n: int = 40) -> float:
    """Small fixed set, tuned by us, so it's a biased and noisy view of reality."""
    return sum(random.random() < TRUE_RATE[variant] + 0.05 for _ in range(n)) / n


def online_ab(n_per_arm: int) -> dict:
    results = {}
    for v, p in TRUE_RATE.items():
        wins = sum(random.random() < p for _ in range(n_per_arm))
        results[v] = (wins, n_per_arm)
    return results


def two_proportion_z(w1, n1, w2, n2) -> float:
    p1, p2, p = w1 / n1, w2 / n2, (w1 + w2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return (p2 - p1) / se


def detection_rate(n_per_arm: int, trials: int = 300) -> float:
    """Run the same A/B test many times; how often does it flag a (real) 4-point improvement?"""
    hits = 0
    for _ in range(trials):
        r = online_ab(n_per_arm)
        (wa, na), (wb, nb) = r["A (current)"], r["B (candidate)"]
        hits += two_proportion_z(wa, na, wb, nb) > 1.96
    return hits / trials


if __name__ == "__main__":
    print("OFFLINE (40 cases each, before shipping), three repeats of the same measurement:")
    for rep in range(3):
        print(f"  run {rep + 1}: " + "  ".join(f"{v} {offline_eval(v):.0%}" for v in TRUE_RATE))
    print("  -> the gap between variants jumps around from run to run: 40 cases is mostly noise\n")

    print("ONLINE A/B: B is truly 4 points better. How often does a test of this size notice?")
    for n in (100, 500, 2000, 10000):
        print(f"  n={n:>5}/arm -> detected in {detection_rate(n):>4.0%} of experiments")

    print("\nSmall samples miss real wins (and sometimes 'find' fake ones). Decide the sample size up front,")
    print("don't stop the test the moment it looks good, and use offline eval to filter, online to confirm.")
    print("Feed online failures back into the offline set.")
