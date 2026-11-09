"""CPU-bound vs I/O-bound: pick the tool by what the work waits on.

I/O-bound work (network, disk) spends its time waiting, so threads overlap the waits.
CPU-bound work needs a core, and in CPython the GIL stops threads from running Python code in
parallel, so you need processes.

Run:
    python cpu_vs_io.py
"""

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def io_task(_: int) -> None:
    time.sleep(0.2)                                  # stands in for a network call


def cpu_task(n: int) -> int:
    return sum(i * i for i in range(n))


def timed(label: str, fn) -> float:
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    print(f"  {label:<28} {elapsed:.2f}s")
    return elapsed


if __name__ == "__main__":
    print("I/O-bound: 8 tasks x 0.2s of waiting")
    timed("sequential", lambda: [io_task(i) for i in range(8)])
    with ThreadPoolExecutor(8) as pool:
        timed("8 threads", lambda: list(pool.map(io_task, range(8))))

    print("\nCPU-bound: 4 tasks of pure computation")
    work = [2_000_000] * 4
    timed("sequential", lambda: [cpu_task(n) for n in work])
    with ThreadPoolExecutor(4) as pool:
        timed("4 threads (GIL-bound)", lambda: list(pool.map(cpu_task, work)))
    with ProcessPoolExecutor(4) as pool:
        timed("4 processes", lambda: list(pool.map(cpu_task, work)))

    print("\nRule of thumb: waiting -> threads or asyncio; computing -> processes (or native code).")
    print("Process startup and pickling cost time, so tiny tasks can be slower in a process pool.")
