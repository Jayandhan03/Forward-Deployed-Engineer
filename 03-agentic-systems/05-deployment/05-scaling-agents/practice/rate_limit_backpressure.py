"""Scaling agents: the bottleneck is the model provider's rate limit, not your CPU.

Shows three controls that keep a burst of runs from becoming a pile of 429s:
  - a concurrency cap (semaphore)       how many model calls in flight at once
  - a token-bucket rate limiter         requests per second to the provider
  - backpressure (bounded queue)        say "busy" early instead of timing out late

Run:
    python rate_limit_backpressure.py
"""

import queue
import threading
import time


class TokenBucket:
    """Allows `rate` calls per second on average, with bursts up to `capacity`."""

    def __init__(self, rate: float, capacity: int):
        self.rate, self.capacity = rate, capacity
        self.tokens, self.updated = float(capacity), time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            time.sleep(wait)


bucket = TokenBucket(rate=20, capacity=5)           # provider allows ~20 req/s
in_flight = threading.Semaphore(4)                  # and we cap parallel calls at 4
inbox: queue.Queue = queue.Queue(maxsize=6)         # bounded: this is the backpressure
stats = {"served": 0, "rejected": 0, "peak": 0, "now": 0}
lock = threading.Lock()


def model_call(run_id: int) -> None:
    bucket.acquire()
    with in_flight:
        with lock:
            stats["now"] += 1
            stats["peak"] = max(stats["peak"], stats["now"])
        time.sleep(0.05)                            # the slow model call
        with lock:
            stats["now"] -= 1
            stats["served"] += 1


def submit(run_id: int) -> bool:
    try:
        inbox.put_nowait(run_id)                    # full queue -> tell the caller now (HTTP 429/503)
        return True
    except queue.Full:
        stats["rejected"] += 1
        return False


def worker() -> None:
    while True:
        run_id = inbox.get()
        if run_id is None:
            return
        model_call(run_id)


if __name__ == "__main__":
    workers = [threading.Thread(target=worker) for _ in range(8)]
    for w in workers:
        w.start()

    start = time.monotonic()
    for i in range(30):                             # a burst of 30 requests at once
        submit(i)
        time.sleep(0.002)
    for _ in workers:
        inbox.put(None)
    for w in workers:
        w.join()

    print(f"burst of 30 -> served {stats['served']}, rejected early {stats['rejected']}")
    print(f"peak concurrent model calls: {stats['peak']} (cap 4, even with 8 workers)")
    print(f"took {time.monotonic() - start:.2f}s")
