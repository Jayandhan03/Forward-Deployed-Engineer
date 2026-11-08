"""Status codes: pick the right one, and know which are safe for a client to retry.

The class tells the client who is at fault and what to do:
  2xx success | 3xx go elsewhere | 4xx YOU got it wrong (don't retry as-is) | 5xx WE failed (maybe retry)

Run:
    python status_codes.py
"""

import time


def classify_error(exc: Exception) -> tuple[int, str]:
    """Map domain errors to codes at the API boundary, not scattered through the code."""
    mapping = {
        KeyError: (404, "not found"),
        PermissionError: (403, "forbidden"),
        ValueError: (422, "validation failed"),
        TimeoutError: (504, "upstream timed out"),
        ConnectionError: (503, "dependency unavailable"),
    }
    for kind, result in mapping.items():
        if isinstance(exc, kind):
            return result
    return 500, "internal error"


RETRYABLE = {408, 429, 500, 502, 503, 504}


def should_retry(status: int, method: str, has_idempotency_key: bool = False) -> bool:
    if status not in RETRYABLE:
        return False                                         # 4xx: fix the request, retrying won't help
    return method in {"GET", "PUT", "DELETE"} or has_idempotency_key    # don't blind-retry plain POST


def backoff_delay(attempt: int, retry_after: float | None = None) -> float:
    if retry_after is not None:
        return retry_after                                   # the server told us exactly how long to wait
    return min(30.0, 0.5 * 2 ** attempt)


if __name__ == "__main__":
    print("domain error -> HTTP code:")
    for e in (KeyError("user 9"), PermissionError(), ValueError("bad email"), TimeoutError(), RuntimeError("bug")):
        code, why = classify_error(e)
        print(f"  {type(e).__name__:<16} -> {code} {why}")

    print("\nshould a client retry?")
    for status, method, key in [(404, "GET", False), (422, "POST", False), (503, "GET", False),
                                (503, "POST", False), (503, "POST", True), (429, "GET", False)]:
        print(f"  {status} on {method:<4}{' (with Idempotency-Key)' if key else '':<24} -> {should_retry(status, method, key)}")

    print("\nbackoff schedule (attempts 0..5):", [backoff_delay(a) for a in range(6)])
    print("429 with Retry-After: 7 ->", backoff_delay(2, retry_after=7))

    print("\nCommon mix-ups: 401 = not logged in, 403 = logged in but not allowed; 400 = malformed, 422 = well-formed")
    print("but invalid; 201 for creates (+ Location header); 204 for success with no body; never 200 with an error body.")
