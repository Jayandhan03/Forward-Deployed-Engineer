"""Wrap flaky tool calls: timeout, retry with backoff + jitter, and a circuit breaker.

Run:
    python resilient_call.py
"""

import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

random.seed(7)
_pool = ThreadPoolExecutor(max_workers=4)


class CircuitOpen(Exception):
    pass


class CircuitBreaker:
    """closed -> (N failures) -> open -> (cooldown) -> half-open -> (success) -> closed."""

    def __init__(self, threshold=3, cooldown_s=0.5):
        self.threshold, self.cooldown_s = threshold, cooldown_s
        self.failures, self.opened_at = 0, None

    def before(self):
        if self.opened_at is not None:
            if time.time() - self.opened_at < self.cooldown_s:
                raise CircuitOpen("circuit open: failing fast, not calling the tool")
            # cooldown over: half-open, let one call through

    def record(self, ok: bool):
        if ok:
            self.failures, self.opened_at = 0, None
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.time()


def call_with_resilience(fn, breaker: CircuitBreaker, *, timeout_s=0.2, retries=2, base_delay=0.05):
    for attempt in range(retries + 1):
        breaker.before()
        try:
            result = _pool.submit(fn).result(timeout=timeout_s)
            breaker.record(True)
            return result
        except (FutureTimeout, ConnectionError) as e:
            breaker.record(False)
            if attempt == retries:
                raise
            delay = base_delay * 2**attempt * random.uniform(0.5, 1.5)   # jitter avoids thundering herd
            print(f"   attempt {attempt + 1} failed ({type(e).__name__}); retry in {delay * 1000:.0f}ms")
            time.sleep(delay)


if __name__ == "__main__":
    state = {"n": 0}

    def flaky():                       # fails twice, then works
        state["n"] += 1
        if state["n"] <= 2:
            raise ConnectionError("upstream 503")
        return "ok"

    def slow():
        time.sleep(1)
        return "too late"

    def dead():
        raise ConnectionError("down")

    print("1. flaky tool, retries recover it:")
    print("  ->", call_with_resilience(flaky, CircuitBreaker()))

    print("2. slow tool, timeout fires:")
    try:
        call_with_resilience(slow, CircuitBreaker(), retries=0)
    except FutureTimeout:
        print("  -> timed out after 0.2s (return an error to the model, don't hang the run)")

    print("3. dead tool, breaker opens and later calls fail fast:")
    breaker = CircuitBreaker(threshold=3)
    for i in range(3):
        try:
            call_with_resilience(dead, breaker, retries=1)
        except (ConnectionError, CircuitOpen) as e:
            print(f"  call {i + 1}: {type(e).__name__}: {e}")
