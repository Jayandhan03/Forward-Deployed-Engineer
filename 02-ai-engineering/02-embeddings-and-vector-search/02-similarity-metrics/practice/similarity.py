"""Similarity metrics on vectors: cosine, dot product, Euclidean, and when they agree or differ.

Pure Python so you can see the formulas. Real embeddings have hundreds or thousands of dimensions;
the math is identical.

Run:
    python similarity.py
"""

import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def cosine(a, b):
    """Angle between vectors, ignoring length. 1 = same direction, 0 = unrelated, -1 = opposite."""
    return dot(a, b) / (norm(a) * norm(b))


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def normalise(a):
    n = norm(a)
    return [x / n for x in a]


if __name__ == "__main__":
    query = [1.0, 1.0]
    docs = {
        "same direction, short": [0.5, 0.5],
        "same direction, long":  [4.0, 4.0],
        "different direction":   [1.0, -1.0],
        "mostly x":              [3.0, 0.5],
    }

    print(f"{'doc':<24}{'cosine':>8}{'dot':>8}{'euclid':>8}")
    for name, v in docs.items():
        print(f"{name:<24}{cosine(query, v):>8.2f}{dot(query, v):>8.2f}{euclidean(query, v):>8.2f}")

    print("\nNotice: the short and long same-direction docs have identical cosine (1.00),")
    print("but dot product and distance are fooled by length.")

    a, b = normalise([3.0, 4.0]), normalise([1.0, 2.0])
    print(f"\nAfter normalising to length 1: cosine={cosine(a, b):.4f}  dot={dot(a, b):.4f}")
    print("-> identical. Most embedding models return normalised vectors, so 'cosine' and 'dot'")
    print("   are the same ranking and dot is cheaper. Check your model's docs, and use the metric")
    print("   your vector index is configured for.")
