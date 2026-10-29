"""Runaway-loop protection: four independent brakes around an agent loop.

  1. max steps          - hard ceiling
  2. repeat detection   - same tool + same args again and again
  3. no-progress        - tool results stop changing
  4. kill switch        - an external flag an operator can flip

Run:
    python loop_guard.py
"""

from collections import Counter


class LoopGuard:
    def __init__(self, max_steps=10, max_repeats=3, patience=4):
        self.max_steps, self.max_repeats, self.patience = max_steps, max_repeats, patience
        self.steps = 0
        self.calls: Counter = Counter()
        self.recent_results: list[str] = []
        self.killed = False          # in production: a Redis key / DB flag checked every step

    def check(self, tool: str, args: dict, result: str | None = None) -> str | None:
        """Return a reason to stop, or None to continue."""
        self.steps += 1
        if self.killed:
            return "kill switch"
        if self.steps > self.max_steps:
            return f"max steps ({self.max_steps})"
        key = (tool, repr(sorted(args.items())))
        self.calls[key] += 1
        if self.calls[key] > self.max_repeats:
            return f"repeated identical call to {tool}"
        if result is not None:
            self.recent_results.append(result)
            tail = self.recent_results[-self.patience:]
            if len(tail) == self.patience and len(set(tail)) == 1:
                return f"no progress: last {self.patience} results identical"
        return None


def simulate(name: str, calls: list[tuple[str, dict, str]], kill_at: int | None = None) -> None:
    guard = LoopGuard()
    for i, (tool, args, result) in enumerate(calls, 1):
        if kill_at == i:
            guard.killed = True
        reason = guard.check(tool, args, result)
        if reason:
            print(f"{name:<22} stopped at step {i}: {reason}")
            return
    print(f"{name:<22} finished normally in {guard.steps} steps")


if __name__ == "__main__":
    healthy = [("search", {"q": f"topic {i}"}, f"result {i}") for i in range(5)]
    stuck_same_call = [("search", {"q": "x"}, f"r{i}") for i in range(10)]
    stuck_new_calls = [("search", {"q": f"try {i}"}, "nothing found") for i in range(10)]
    endless_varied = [("search", {"q": f"q{i}"}, f"r{i}") for i in range(30)]

    simulate("healthy run", healthy)
    simulate("same call repeated", stuck_same_call)
    simulate("different args, no news", stuck_new_calls)
    simulate("endless but 'progressing'", endless_varied)
    simulate("operator kills it", healthy, kill_at=3)
