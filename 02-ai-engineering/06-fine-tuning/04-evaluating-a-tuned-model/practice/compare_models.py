"""Evaluating a tuned model: compare against the baseline on a held-out set, check for regressions.

Three questions: did it improve on the target task? did it get worse on anything else? is the gain
bigger than noise? Models are stand-ins so this runs offline.

Run:
    python compare_models.py
"""

import math
import random

random.seed(4)

# (case id, slice, base_correct, tuned_correct) on a held-out test set the tuning never saw.
random_cases = []
for i in range(120):
    random_cases.append((f"t{i}", "target_task", random.random() < 0.70, random.random() < 0.86))
for i in range(60):
    random_cases.append((f"g{i}", "general_ability", random.random() < 0.90, random.random() < 0.83))   # forgetting
for i in range(30):
    random_cases.append((f"s{i}", "safety", random.random() < 0.97, random.random() < 0.97))


def rate(rows, idx):
    return sum(r[idx] for r in rows) / len(rows)


def sign_test_p(wins: int, losses: int) -> float:
    """Two-sided exact sign test on discordant pairs: is 'tuned better' more than a coin flip?"""
    n = wins + losses
    if n == 0:
        return 1.0
    k = max(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2**n
    return min(1.0, 2 * tail)


if __name__ == "__main__":
    print(f"{'slice':<17}{'n':>4}{'base':>7}{'tuned':>7}{'delta':>7}  wins/losses  p-value")
    for name in ("target_task", "general_ability", "safety"):
        rows = [r for r in random_cases if r[1] == name]
        wins = sum(1 for r in rows if r[3] and not r[2])       # tuned right, base wrong
        losses = sum(1 for r in rows if r[2] and not r[3])     # base right, tuned wrong
        d = rate(rows, 3) - rate(rows, 2)
        print(f"{name:<17}{len(rows):>4}{rate(rows, 2):>7.0%}{rate(rows, 3):>7.0%}{d:>+7.0%}  "
              f"{wins:>4}/{losses:<6} {sign_test_p(wins, losses):>7.3f}")

    print("\nRead it slice by slice: a big win on the target task can hide forgetting elsewhere.")
    print("Ship only if the target gain is real (small p), nothing important regressed, and the gain")
    print("justifies the cost of owning a tuned model. Also compare against a well-prompted baseline,")
    print("not just the raw base model.")
