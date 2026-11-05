"""LoRA in numbers: why training a low-rank update is so much cheaper than full fine-tuning.

Instead of updating a big weight matrix W (d x k), LoRA freezes W and learns two small matrices
A (d x r) and B (r x k), using W + A @ B. Trainable parameters drop from d*k to r*(d+k).

Pure Python; no GPU or model needed.

Run:
    python lora_math.py
"""

import random

random.seed(2)


def params_full(d: int, k: int) -> int:
    return d * k


def params_lora(d: int, k: int, r: int) -> int:
    return r * (d + k)


def matmul(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def rank_demo():
    """A tiny numeric check that A (d x r) @ B (r x k) is a full-size update of rank <= r."""
    d, k, r = 6, 6, 2
    A = [[random.gauss(0, 1) for _ in range(r)] for _ in range(d)]
    B = [[random.gauss(0, 1) for _ in range(k)] for _ in range(r)]
    delta = matmul(A, B)
    print(f"A is {d}x{r}, B is {r}x{k} -> A@B is {len(delta)}x{len(delta[0])} "
          f"using {r * (d + k)} numbers instead of {d * k}")


if __name__ == "__main__":
    rank_demo()

    # A 7B-ish transformer: say 32 layers, each adapting 4 attention matrices of 4096 x 4096.
    layers, mats, d = 32, 4, 4096
    full = layers * mats * params_full(d, d)
    print(f"\nAdapting {layers * mats} matrices of {d}x{d}:")
    print(f"  full fine-tuning of these:   {full / 1e6:8.1f}M trainable params")
    for r in (4, 8, 16, 64):
        lora = layers * mats * params_lora(d, d, r)
        print(f"  LoRA rank {r:<3}:              {lora / 1e6:8.2f}M  ({lora / full:.2%} of full)")

    print("\nAdapter file size is tiny (MBs), so you can keep one base model and swap adapters per task/customer.")
    print("Higher rank = more capacity but more params and overfitting risk; 8-16 is a common start.")
    print("QLoRA = the same idea with the frozen base model quantised to 4-bit to fit in less memory.")
