"""Race conditions and deadlocks, made deterministic so you can see them.

Race: read-modify-write is not atomic, so two threads can overwrite each other's update.
Deadlock: two threads each hold one lock and wait for the other's. Fix: one global lock order.

Run:
    python races_and_deadlocks.py
"""

import threading
import time


def demo_race() -> None:
    balance = 100
    lock = threading.Lock()

    def withdraw_unsafe(amount: int) -> None:
        nonlocal balance
        current = balance                    # read
        time.sleep(0.05)                     # another thread runs here (forces the bad interleaving)
        balance = current - amount           # write back a stale value

    def withdraw_safe(amount: int) -> None:
        nonlocal balance
        with lock:                           # the whole read-modify-write is one critical section
            current = balance
            time.sleep(0.05)
            balance = current - amount

    for name, fn in (("unsafe", withdraw_unsafe), ("safe  ", withdraw_safe)):
        balance = 100
        threads = [threading.Thread(target=fn, args=(30,)) for _ in range(2)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        print(f"  {name}: 100 - 30 - 30 = {balance}  (expected 40)")


def demo_deadlock() -> None:
    a, b = threading.Lock(), threading.Lock()
    both_hold_one = threading.Barrier(2)

    def worker(first: threading.Lock, second: threading.Lock, name: str, results: dict) -> None:
        with first:
            both_hold_one.wait()             # each thread now holds its first lock
            got = second.acquire(timeout=0.5)    # a real program would wait forever here
            results[name] = "acquired both" if got else "DEADLOCK (timed out waiting)"
            if got:
                second.release()

    print("  opposite lock order:")
    results: dict = {}
    t1 = threading.Thread(target=worker, args=(a, b, "t1", results))
    t2 = threading.Thread(target=worker, args=(b, a, "t2", results))
    [t.start() for t in (t1, t2)]
    [t.join() for t in (t1, t2)]
    print("   ", results)

    print("  same lock order (a then b everywhere):")
    results = {}
    both_hold_one.reset()

    def ordered(name: str) -> None:
        with a:
            with b:
                results[name] = "acquired both"

    ts = [threading.Thread(target=ordered, args=(n,)) for n in ("t1", "t2")]
    [t.start() for t in ts]
    [t.join() for t in ts]
    print("   ", results)


if __name__ == "__main__":
    print("1. race condition (lost update):")
    demo_race()
    print("\n2. deadlock:")
    demo_deadlock()
    print("\nRules: protect shared mutable state with a lock or avoid sharing it (queues, immutability);")
    print("always acquire multiple locks in one fixed order; use timeouts so hangs become errors.")
