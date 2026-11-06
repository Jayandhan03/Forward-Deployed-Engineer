"""Processes vs threads: what is shared, what is isolated, and what the OS gives each.

  - A process has its own memory. A child's changes never reach the parent.
  - Threads share memory, so they can race without a lock.

Run:
    python processes_and_threads.py
"""

import multiprocessing
import os
import threading

counter = 0


def bump_in_child(q):
    global counter
    counter += 1000                              # changes the CHILD's copy only
    q.put((os.getpid(), counter))


def unsafe_add(n):
    global counter
    for _ in range(n):
        counter += 1                             # read-modify-write: not atomic


def safe_add(n, lock):
    global counter
    for _ in range(n):
        with lock:
            counter += 1


if __name__ == "__main__":
    print(f"parent pid={os.getpid()}, cpus={os.cpu_count()}")

    print("\n1. PROCESS isolation:")
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=bump_in_child, args=(q,))
    p.start()
    child_pid, child_val = q.get()
    p.join()
    print(f"   child pid={child_pid} saw counter={child_val}; parent's counter is still {counter}")

    print("\n2. THREADS share memory:")
    for label, make in [("no lock", lambda: unsafe_add), ("with lock", lambda: safe_add)]:
        counter = 0
        lock = threading.Lock()
        if label == "no lock":
            ts = [threading.Thread(target=unsafe_add, args=(200_000,)) for _ in range(4)]
        else:
            ts = [threading.Thread(target=safe_add, args=(200_000, lock)) for _ in range(4)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        print(f"   {label:<10} expected 800000, got {counter}")

    print("\nNote: whether the unlocked run loses updates depends on the Python version and timing;")
    print("the code is still wrong either way. Threads: shared + fast + needs locks. Processes: isolated + heavier.")
