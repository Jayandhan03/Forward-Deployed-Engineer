"""Online monitoring: rolling-window metrics over recent runs, with alert rules.

Watch rates and percentiles over a window, not single events.

Run:
    python monitor.py
"""

import random
from collections import deque
from dataclasses import dataclass

random.seed(3)


@dataclass
class RunResult:
    ok: bool
    latency_s: float
    cost_usd: float
    tool_errors: int


class Monitor:
    def __init__(self, window=50):
        self.runs: deque[RunResult] = deque(maxlen=window)    # old runs fall off automatically

    def record(self, r: RunResult) -> None:
        self.runs.append(r)

    def snapshot(self) -> dict:
        n = len(self.runs)
        lat = sorted(r.latency_s for r in self.runs)
        return {
            "runs": n,
            "success_rate": sum(r.ok for r in self.runs) / n,
            "p95_latency_s": lat[int(0.95 * (n - 1))],
            "avg_cost_usd": sum(r.cost_usd for r in self.runs) / n,
            "tool_error_rate": sum(r.tool_errors > 0 for r in self.runs) / n,
        }

    def alerts(self) -> list[str]:
        s, out = self.snapshot(), []
        if s["runs"] < 20:
            return out                                        # too little data to judge
        if s["success_rate"] < 0.90:
            out.append(f"success rate {s['success_rate']:.0%} < 90%")
        if s["p95_latency_s"] > 8:
            out.append(f"p95 latency {s['p95_latency_s']:.1f}s > 8s")
        if s["avg_cost_usd"] > 0.05:
            out.append(f"avg cost ${s['avg_cost_usd']:.3f} > $0.05")
        if s["tool_error_rate"] > 0.15:
            out.append(f"tool error rate {s['tool_error_rate']:.0%} > 15%")
        return out


def fake_run(degraded: bool) -> RunResult:
    p_fail = 0.3 if degraded else 0.03
    return RunResult(ok=random.random() > p_fail,
                     latency_s=random.uniform(1, 5) * (2 if degraded else 1),
                     cost_usd=random.uniform(0.01, 0.04),
                     tool_errors=int(random.random() < (0.3 if degraded else 0.05)))


if __name__ == "__main__":
    m = Monitor()
    for i in range(1, 101):
        degraded = i > 60                                     # something breaks after run 60
        m.record(fake_run(degraded))
        if i % 20 == 0:
            alerts = m.alerts()
            print(f"after run {i:>3}: {'ALERT ' + '; '.join(alerts) if alerts else 'healthy'}")
