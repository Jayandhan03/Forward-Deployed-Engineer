"""Cost model: $ per run, where it concentrates, and what caching and a cheaper model save.

Prices and token counts are ILLUSTRATIVE. Replace PRICES with your provider's current rates and
the run profile with numbers measured from your own traces.

Run:
    python cost_model.py
"""

# USD per million tokens (example numbers only)
PRICES = {
    "big":   {"in": 3.00, "out": 15.00, "cached_in": 0.30},
    "small": {"in": 0.80, "out": 4.00,  "cached_in": 0.08},
}

# A typical run: (step, model, input_tokens, output_tokens, cacheable_prefix_tokens)
RUN = [
    ("plan",     "big",   3000, 400, 2500),
    ("tool_1",   "small", 3600, 150, 2500),
    ("tool_2",   "small", 4300, 150, 2500),
    ("tool_3",   "small", 5000, 150, 2500),
    ("synthesize", "big", 6000, 600, 2500),
]


def step_cost(model, tin, tout, cached=0, use_cache=False):
    p = PRICES[model]
    fresh = tin - (cached if use_cache else 0)
    cached_part = cached if use_cache else 0
    return (fresh * p["in"] + cached_part * p["cached_in"] + tout * p["out"]) / 1e6


def run_cost(steps, use_cache=False, force_model=None):
    rows = [(n, step_cost(force_model or m, i, o, c, use_cache)) for n, m, i, o, c in steps]
    return rows, sum(c for _, c in rows)


if __name__ == "__main__":
    rows, base = run_cost(RUN)
    print("per-step cost (no caching):")
    for name, c in rows:
        print(f"  {name:<11} ${c:.4f}  {'#' * int(c / base * 40)}")
    print(f"  TOTAL       ${base:.4f} per run\n")

    _, cached = run_cost(RUN, use_cache=True)
    _, all_big = run_cost(RUN, force_model="big")
    print(f"with prompt caching:       ${cached:.4f}  ({1 - cached / base:.0%} cheaper)")
    print(f"if every step used 'big':  ${all_big:.4f}  ({all_big / base:.1f}x more)\n")

    for runs_per_day in (1_000, 50_000):
        print(f"{runs_per_day:>6} runs/day -> ${base * runs_per_day:>9,.2f}/day, ${base * runs_per_day * 30:>11,.0f}/month")
    print("\nContext grows each step, so long runs get quadratically pricey: cap steps and trim context.")
