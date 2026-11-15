"""Rate limiting: cap how often a client can call you (abuse, cost control, fairness).

Algorithm here: token bucket. A bucket holds up to `capacity` tokens and refills at `rate` per
second; each request spends one. Allows short bursts but enforces the average. In-memory = single
process only; with several instances use Redis (see 05-redis/04-rate-limiter). On limit: HTTP 429
plus a Retry-After header.

Needs: pip install fastapi httpx      Run:  python rate-limiting.py
"""

import time

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


class TokenBucket:
    def __init__(self, capacity: int, rate: float, clock=time.monotonic):
        self.capacity, self.rate, self.clock = capacity, rate, clock
        self.tokens, self.updated = float(capacity), clock()

    def take(self) -> tuple[bool, float]:
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)   # refill
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True, 0.0
        return False, (1 - self.tokens) / self.rate          # seconds until one token is available


class RateLimiter:
    def __init__(self, capacity: int, rate: float, clock=time.monotonic):
        self.buckets: dict[str, TokenBucket] = {}
        self.capacity, self.rate, self.clock = capacity, rate, clock

    def check(self, key: str) -> tuple[bool, float]:
        bucket = self.buckets.setdefault(key, TokenBucket(self.capacity, self.rate, self.clock))
        return bucket.take()


class Clock:                                                 # fake clock: tests don't need real sleeps
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


clock = Clock()
limiter = RateLimiter(capacity=3, rate=1.0, clock=clock)    # burst of 3, then 1 request/second
app = FastAPI()


def rate_limit(request: Request):                            # as a dependency: apply per route, or per router
    key = request.headers.get("x-api-key") or request.client.host     # prefer API key / user id over IP
    allowed, retry_after = limiter.check(key)
    if not allowed:
        raise TooMany(retry_after)


class TooMany(Exception):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after


@app.exception_handler(TooMany)
async def too_many(request: Request, exc: TooMany):
    return JSONResponse({"error": "rate limit exceeded"}, status_code=429,
                        headers={"Retry-After": str(int(exc.retry_after) + 1)})


@app.get("/search", dependencies=[Depends(rate_limit)])
def search():
    return {"ok": True}


if __name__ == "__main__":
    c = TestClient(app)
    print("burst :", [c.get("/search", headers={"X-API-Key": "alice"}).status_code for _ in range(5)])
    r = c.get("/search", headers={"X-API-Key": "alice"})
    print("limited:", r.status_code, r.json(), "Retry-After:", r.headers["retry-after"])
    print("other client unaffected:", c.get("/search", headers={"X-API-Key": "bob"}).status_code)
    clock.now += 2                                           # 2 seconds pass -> 2 tokens refilled
    print("after 2s:", [c.get("/search", headers={"X-API-Key": "alice"}).status_code for _ in range(3)])

    print("\nPick key = user/API key (not just IP: NATs share IPs, attackers rotate them). Tighter limits on login and")
    print("expensive LLM endpoints. Also seen: fixed window (simple, bursty at edges), sliding window (smoother).")
    print("Production: Redis (atomic INCR/Lua) so all instances share counts; often enforced at the gateway/CDN too.")
