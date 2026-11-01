"""Queue-backed workers: the API enqueues a run and returns an id; workers pull, execute, report.

Uses threads and queue.Queue to show the shape; in production the queue is Redis/SQS/Postgres.
Includes the parts that matter: retries, a dead-letter queue, and an idempotency check.

Run:
    python worker_queue.py
"""

import queue
import threading
import time

jobs: queue.Queue = queue.Queue()
dead_letter: list[dict] = []
results: dict[str, str] = {}
done_ids: set[str] = set()                 # idempotency: never run the same job twice
lock = threading.Lock()
MAX_ATTEMPTS = 3


def enqueue(run_id: str, task: str) -> str:
    jobs.put({"run_id": run_id, "task": task, "attempts": 0})
    return run_id                            # the API returns immediately; client polls or streams


def run_agent(task: str, attempt: int) -> str:
    time.sleep(0.05)
    if "flaky" in task and attempt == 1:             # transient: succeeds on retry
        raise ConnectionError("provider 529")
    if "poison" in task:
        raise ValueError("cannot parse task")
    return f"done: {task}"


def worker():
    while True:
        job = jobs.get()
        if job is None:
            return
        try:
            with lock:
                if job["run_id"] in done_ids:    # duplicate delivery (at-least-once queues do this)
                    continue                     # finally below still marks the job done
            job["attempts"] += 1
            try:
                out = run_agent(job["task"], job["attempts"])
                with lock:
                    results[job["run_id"]] = out
                    done_ids.add(job["run_id"])
            except Exception as e:
                if job["attempts"] >= MAX_ATTEMPTS:
                    dead_letter.append({**job, "error": repr(e)})    # park it for a human
                else:
                    jobs.put(job)                                    # retry
        finally:
            jobs.task_done()


if __name__ == "__main__":
    threads = [threading.Thread(target=worker, name=f"worker-{i}") for i in (1, 2)]
    for t in threads:
        t.start()

    for i, task in enumerate(["summarise q3", "flaky lookup", "poison pill", "draft email"]):
        enqueue(f"run-{i}", task)
    enqueue("run-0", "summarise q3")          # duplicate delivery, must be ignored

    jobs.join()
    for _ in threads:
        jobs.put(None)
    for t in threads:
        t.join()

    for run_id in sorted(results):
        print(run_id, "->", results[run_id])
    print("dead letter:", [(d["run_id"], d["error"]) for d in dead_letter])
