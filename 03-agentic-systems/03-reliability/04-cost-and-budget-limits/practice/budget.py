"""Cost limits at three levels: per run, per user per day, and a global ceiling. Hard stop.

Prices are illustrative placeholders; load real ones from config.

Run:
    python budget.py
"""

from collections import defaultdict

PRICE_PER_MTOK = {"input": 3.00, "output": 15.00}   # USD per million tokens (example numbers)


def cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * PRICE_PER_MTOK["input"] + output_tokens * PRICE_PER_MTOK["output"]) / 1e6


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, per_run=0.05, per_user_day=0.20, global_day=1.00):
        self.per_run, self.per_user_day, self.global_day = per_run, per_user_day, global_day
        self.user_spend: dict[str, float] = defaultdict(float)
        self.global_spend = 0.0

    def start_run(self, user: str) -> "RunMeter":
        return RunMeter(self, user)


class RunMeter:
    def __init__(self, budget: Budget, user: str):
        self.b, self.user, self.spent = budget, user, 0.0

    def charge(self, input_tokens: int, output_tokens: int) -> None:
        """Call after every model response. Raises BEFORE the next call can happen."""
        c = cost(input_tokens, output_tokens)
        self.spent += c
        self.b.user_spend[self.user] += c
        self.b.global_spend += c
        if self.spent > self.b.per_run:
            raise BudgetExceeded(f"run budget ${self.b.per_run:.2f} hit (spent ${self.spent:.3f})")
        if self.b.user_spend[self.user] > self.b.per_user_day:
            raise BudgetExceeded(f"{self.user} daily budget ${self.b.per_user_day:.2f} hit")
        if self.b.global_spend > self.b.global_day:
            raise BudgetExceeded("global daily ceiling hit")


if __name__ == "__main__":
    budget = Budget()

    # Context grows every turn, so cost per step grows too: that's why loops get expensive fast.
    run = budget.start_run("alice")
    context = 2_000
    for step in range(1, 30):
        try:
            run.charge(input_tokens=context, output_tokens=400)
        except BudgetExceeded as e:
            print(f"step {step}: STOP - {e}")
            break
        print(f"step {step}: context={context:>6} tokens, run total ${run.spent:.4f}")
        context += 3_000

    print("\nalice today:", f"${budget.user_spend['alice']:.4f}")
