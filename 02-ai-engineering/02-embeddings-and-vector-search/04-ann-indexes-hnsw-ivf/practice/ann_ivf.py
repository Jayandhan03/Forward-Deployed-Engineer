"""Approximate nearest neighbour search, the IVF idea from scratch.

Exact search compares the query to every vector: O(N). IVF clusters the vectors first, then at query
time only searches the few clusters nearest the query. Faster, but it can miss the true neighbour:
that trade-off (recall vs speed) is the whole topic. HNSW makes the same trade with a graph instead.

Run:
    python ann_ivf.py
"""

import math
import random

random.seed(1)
DIM, N, CLUSTERS = 16, 4000, 40


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def make_data():
    centres = [[random.gauss(0, 3) for _ in range(DIM)] for _ in range(CLUSTERS)]
    return [[c + random.gauss(0, 1) for c in random.choice(centres)] for _ in range(N)]


def kmeans(vectors, k, iters=8):
    centroids = random.sample(vectors, k)
    for _ in range(iters):
        buckets = [[] for _ in range(k)]
        for i, v in enumerate(vectors):
            buckets[min(range(k), key=lambda c: dist(v, centroids[c]))].append(i)
        for c, members in enumerate(buckets):
            if members:
                centroids[c] = [sum(vectors[i][d] for i in members) / len(members) for d in range(DIM)]
    return centroids, buckets


def exact_search(vectors, q, top=10):
    return sorted(range(len(vectors)), key=lambda i: dist(vectors[i], q))[:top], len(vectors)


def ivf_search(vectors, centroids, buckets, q, nprobe, top=10):
    nearest = sorted(range(len(centroids)), key=lambda c: dist(q, centroids[c]))[:nprobe]
    candidates = [i for c in nearest for i in buckets[c]]
    return sorted(candidates, key=lambda i: dist(vectors[i], q))[:top], len(candidates)


if __name__ == "__main__":
    vectors = make_data()
    centroids, buckets = kmeans(vectors, CLUSTERS)
    queries = [[random.gauss(0, 3) for _ in range(DIM)] for _ in range(30)]

    print(f"{N} vectors, {CLUSTERS} clusters. Exact search compares against all {N}.\n")
    print(f"{'nprobe':>7} {'compared (avg)':>16} {'recall@10':>10}")
    for nprobe in (1, 2, 4, 8, 16):
        recalls, compared = [], []
        for q in queries:
            truth, _ = exact_search(vectors, q)
            found, n = ivf_search(vectors, centroids, buckets, q, nprobe)
            recalls.append(len(set(truth) & set(found)) / 10)
            compared.append(n)
        print(f"{nprobe:>7} {sum(compared) / len(compared):>16.0f} {sum(recalls) / len(recalls):>10.0%}")

    print("\nMore probes -> higher recall, more work. Pick the cheapest setting that meets your recall target.")
