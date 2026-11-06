"""Why memory access pattern matters: the cache rewards sequential access.

Sums the same numbers two ways. Sequential walks memory in order; strided jumps around so most
reads miss the cache. Python adds interpreter overhead, so we use the `array` module and large
strides to make the memory effect visible. Exact numbers vary by machine.

Run:
    python cache_locality.py
"""

import array
import time

N = 1 << 22                       # ~4M ints, ~16 MB: bigger than typical L2 cache
data = array.array("i", range(N))


def sum_with_stride(stride: int) -> int:
    """Visit every element exactly once, but in a stride-sized hop pattern."""
    total = 0
    for start in range(stride):
        for i in range(start, N, stride):
            total += data[i]
    return total


def timed(label: str, stride: int) -> float:
    t = time.perf_counter()
    result = sum_with_stride(stride)
    dt = time.perf_counter() - t
    print(f"  {label:<26} {dt:6.2f}s   (sum={result})")
    return dt


if __name__ == "__main__":
    print(f"summing {N:,} ints, every element once:")
    seq = timed("sequential (stride 1)", 1)
    mid = timed("stride 64 (cache line+)", 64)
    big = timed("stride 4096 (page-sized)", 4096)
    print(f"\nsame work, same answer: stride 4096 is {big / seq:.1f}x the time of sequential")
    print("\nThe hierarchy, roughly: registers ~1 cycle, L1 ~4, L2 ~12, L3 ~40, RAM ~200+, SSD ~100,000+.")
    print("Hardware loads whole 64-byte cache lines, so using neighbours is nearly free.")
    print("This is why arrays beat linked lists and why row-major vs column-major loops can differ 10x.")
