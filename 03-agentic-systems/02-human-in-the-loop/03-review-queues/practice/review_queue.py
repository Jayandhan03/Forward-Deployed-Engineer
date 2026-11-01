"""Review queue: agent actions wait for human sign-off, ordered by risk, with claims and SLAs.

Run:
    python review_queue.py
"""

import itertools
import time
from dataclasses import dataclass, field

SLA_S = {"high": 60, "medium": 300, "low": 3600}
PRIORITY = {"high": 0, "medium": 1, "low": 2}
_seq = itertools.count()


@dataclass
class Item:
    risk: str
    summary: str
    created: float = field(default_factory=time.time)
    claimed_by: str | None = None
    status: str = "pending"
    seq: int = field(default_factory=lambda: next(_seq))

    def sort_key(self) -> tuple:
        return (PRIORITY[self.risk], self.seq)             # risk first, then FIFO

    def overdue(self, now: float) -> bool:
        return now - self.created > SLA_S[self.risk]


class ReviewQueue:
    def __init__(self):
        self.items: list[Item] = []

    def submit(self, risk: str, summary: str, created: float | None = None) -> Item:
        item = Item(risk, summary, created or time.time())
        self.items.append(item)
        return item

    def claim(self, reviewer: str) -> Item | None:
        """Take the most urgent unclaimed item. Claiming stops two reviewers doing the same one."""
        pending = [i for i in self.items if i.status == "pending"]
        if not pending:
            return None
        item = min(pending, key=Item.sort_key)
        item.status, item.claimed_by = "claimed", reviewer
        return item

    def resolve(self, item: Item, verdict: str) -> None:
        item.status = verdict

    def overdue(self) -> list[Item]:
        now = time.time()
        return [i for i in self.items if i.status in ("pending", "claimed") and i.overdue(now)]


if __name__ == "__main__":
    q = ReviewQueue()
    q.submit("low", "update ticket tags")
    q.submit("high", "refund $900 to customer 77")
    q.submit("medium", "email vendor about contract")
    q.submit("high", "delete account 12", created=time.time() - 120)     # waiting too long

    print("overdue (SLA breached):", [i.summary for i in q.overdue()])
    print()
    for reviewer in ("ana", "ben", "ana", "ben"):
        item = q.claim(reviewer)
        q.resolve(item, "approved")
        print(f"{reviewer} reviewed [{item.risk:<6}] {item.summary}")
