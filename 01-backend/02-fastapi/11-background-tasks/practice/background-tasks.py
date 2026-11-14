"""Background tasks: do slow work AFTER the response is sent.

`BackgroundTasks` runs a function in the same process once the response has gone out: good for
"send welcome email", "write audit log", "warm a cache". It is NOT a queue: no retries, lost if
the process dies, shares your CPU. Anything important or heavy goes to a worker (RQ / Celery / ARQ).

Needs: pip install fastapi httpx      Run:  python background-tasks.py
"""

import time

from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
log: list[str] = []


def send_email(to: str, delay: float = 0.3) -> None:
    time.sleep(delay)                                    # pretend SMTP call (sync def -> runs in thread pool)
    log.append(f"email sent to {to}")


def audit(event: str) -> None:
    log.append(f"audit: {event}")


@app.post("/signup")
def signup(email: str, background: BackgroundTasks):
    log.append("user saved")                             # do the essential work first (and commit it!)
    background.add_task(send_email, email)               # args are passed through; runs after the response
    background.add_task(audit, f"signup {email}")        # several tasks run in order
    return {"status": "created"}                         # client gets this immediately


@app.post("/signup-slow")
def signup_slow(email: str):
    send_email(email)                                    # inline: the user waits for the email
    return {"status": "created"}


if __name__ == "__main__":
    c = TestClient(app)

    t = time.perf_counter()
    c.post("/signup-slow?email=a@x.com")
    inline = time.perf_counter() - t

    log.clear()
    t = time.perf_counter()
    r = c.post("/signup?email=b@x.com")                  # TestClient waits for tasks, but real clients don't
    print("response:", r.json())
    print("log order:", log)
    print(f"inline email = {inline:.2f}s of waiting; with a background task the response is sent first")
    print("(TestClient blocks until tasks finish, so here both take about the same: in prod only inline waits.)")

    print("\nUse BackgroundTasks for: best-effort, fast, loss-tolerable side effects (emails, logs, cache warm).")
    print("Use a real queue (Redis + RQ/Celery) when: it must not be lost, needs retries, is heavy/long, or should")
    print("scale on separate workers. Make tasks idempotent and give them their own DB session (the request's is closed).")
