"""Tamper-evident audit trail: each record includes the hash of the previous one.

Run:
    python audit_log.py
"""

import hashlib
import json
import time


class AuditLog:
    def __init__(self):
        self.records: list[dict] = []

    def append(self, **event) -> None:
        prev = self.records[-1]["hash"] if self.records else "genesis"
        record = {"ts": time.time(), "prev": prev, **event}
        record["hash"] = self._hash(record)
        self.records.append(record)

    @staticmethod
    def _hash(record: dict) -> str:
        body = {k: v for k, v in record.items() if k != "hash"}
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

    def verify(self) -> int | None:
        """Return the index of the first broken record, or None if the chain is intact."""
        prev = "genesis"
        for i, r in enumerate(self.records):
            if r["prev"] != prev or r["hash"] != self._hash(r):
                return i
            prev = r["hash"]
        return None


if __name__ == "__main__":
    log = AuditLog()
    # What an auditor asks: who, on whose behalf, which model + prompt version, what, and the outcome.
    common = {"agent": "claims-agent", "model": "claude-sonnet-5-5", "prompt_version": "v14"}
    log.append(**common, user="alice", tool="get_claim", decision="allow")
    log.append(**common, user="alice", tool="approve_payout", amount=900, decision="approved_by:bob")
    log.append(**common, user="alice", tool="send_email", decision="allow")

    print("intact chain    ->", "OK" if log.verify() is None else f"broken at {log.verify()}")

    log.records[1]["amount"] = 9   # someone quietly edits history
    print("after tampering -> broken at record", log.verify())
    print("\nIn production: append-only storage (WORM / object lock), hash anchored externally.")
