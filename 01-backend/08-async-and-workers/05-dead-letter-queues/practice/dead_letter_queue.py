"""Dead-letter queues: park poison messages instead of retrying them forever.

A job that always fails would block or loop. After N attempts it moves to a dead-letter queue
(DLQ) with the error, where a human can inspect it and replay it once the bug is fixed.

Run:
    python dead_letter_queue.py
"""

from collections import deque

MAX_ATTEMPTS = 3
queue: deque = deque()
dlq: list[dict] = []
processed: list[int] = []


def handler(job: dict) -> None:
    if job["payload"] == "poison":
        raise ValueError("cannot parse payload")      # will never succeed
    processed.append(job["id"])


def run() -> None:
    while queue:
        job = queue.popleft()
        job["attempts"] += 1
        try:
            handler(job)
        except Exception as exc:
            if job["attempts"] >= MAX_ATTEMPTS:
                dlq.append({**job, "error": str(exc)})            # park it, keep the queue moving
                print(f"  job {job['id']} -> DLQ after {job['attempts']} attempts ({exc})")
            else:
                print(f"  job {job['id']} failed (attempt {job['attempts']}), requeue")
                queue.append(job)


if __name__ == "__main__":
    for i, payload in enumerate(["ok", "poison", "ok", "ok"], start=1):
        queue.append({"id": i, "payload": payload, "attempts": 0})

    print("processing:")
    run()
    print("\nprocessed:", processed, "| dead-lettered:", [j["id"] for j in dlq])

    print("\nafter the bug is fixed, replay the DLQ:")
    for job in dlq:
        job["payload"] = "ok"
        job["attempts"] = 0
        queue.append(job)
    dlq.clear()
    run()
    print("processed:", processed, "| dead-lettered:", len(dlq))

    print("\nRules: cap attempts, keep the error and original payload, alert on DLQ depth, make handlers")
    print("idempotent so replays are safe.")
