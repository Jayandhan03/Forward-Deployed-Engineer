"""Long-term memory: write facts with metadata, retrieve by relevance + recency, and forget.

Retrieval here is word overlap so it runs offline; swap in embeddings for real use
(see 02-ai-engineering embeddings).

Run:
    python memory_store.py
"""

import re
import time
from dataclasses import dataclass, field


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass
class Memory:
    text: str
    user: str
    created: float = field(default_factory=time.time)
    hits: int = 0


class MemoryStore:
    def __init__(self, ttl_s: float = 30 * 86400):
        self.items: list[Memory] = []
        self.ttl_s = ttl_s

    def remember(self, user: str, text: str) -> None:
        # Don't store duplicates: update the existing memory instead.
        for m in self.items:
            if m.user == user and words(m.text) == words(text):
                m.created = time.time()
                return
        self.items.append(Memory(text, user))

    def recall(self, user: str, query: str, k: int = 2) -> list[str]:
        q, now = words(query), time.time()
        scored = []
        for m in self.items:
            if m.user != user:                       # isolation: never cross users
                continue
            overlap = len(q & words(m.text)) / (len(q) or 1)
            recency = 1 / (1 + (now - m.created) / 86400)
            if overlap > 0:
                scored.append((overlap + 0.1 * recency, m))
        top = sorted(scored, key=lambda p: -p[0])[:k]
        for _, m in top:
            m.hits += 1
        return [m.text for _, m in top]

    def forget(self, user: str) -> int:
        """Right-to-erasure: drop everything about one user."""
        before = len(self.items)
        self.items = [m for m in self.items if m.user != user]
        return before - len(self.items)

    def expire(self) -> int:
        cutoff = time.time() - self.ttl_s
        before = len(self.items)
        self.items = [m for m in self.items if m.created >= cutoff]
        return before - len(self.items)


if __name__ == "__main__":
    store = MemoryStore()
    store.remember("alice", "Alice prefers invoices as PDF")
    store.remember("alice", "Alice works in the London office")
    store.remember("alice", "Alice prefers invoices as PDF")      # duplicate, not stored twice
    store.remember("bob", "Bob prefers invoices as CSV")

    print("memories stored:", len(store.items))
    print("alice, 'what format for invoices?' ->", store.recall("alice", "what format for invoices?"))
    print("bob,   'what format for invoices?' ->", store.recall("bob", "what format for invoices?"))
    print("forget alice -> removed", store.forget("alice"), "| left:", len(store.items))
