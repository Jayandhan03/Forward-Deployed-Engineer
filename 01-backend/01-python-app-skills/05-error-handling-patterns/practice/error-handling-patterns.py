"""Error handling patterns: domain errors inside, safe messages outside, retry only what's transient.

Three ideas:
  1. A small exception hierarchy; each error knows its HTTP status + a user-safe message.
  2. One boundary (the router / exception handler) turns exceptions into responses and logs the detail.
  3. Retry transient infrastructure errors with backoff; never retry business errors.

Run:
    python error-handling-patterns.py
"""

import time


# --- 1. hierarchy -------------------------------------------------------------------------------
class AppError(Exception):
    status = 500
    public_message = "Something went wrong"          # safe to show users


class NotFound(AppError):
    status = 404
    public_message = "Resource not found"


class InsufficientFunds(AppError):                   # domain error: a rule was violated
    status = 422
    public_message = "Insufficient funds"


class TransientError(Exception):                     # infrastructure: timeout, 503, dropped connection
    pass


# --- 3. retry only transient failures -----------------------------------------------------------
def retry(fn, attempts=3, base_delay=0.01):
    for i in range(attempts):
        try:
            return fn()
        except TransientError:
            if i == attempts - 1:
                raise                                 # out of attempts: let it bubble up
            time.sleep(base_delay * 2**i)             # exponential backoff


# --- business code: raises meaningful errors, knows nothing about HTTP --------------------------
BALANCES = {"alice": 50}


def withdraw(user: str, amount: int) -> int:
    if user not in BALANCES:
        raise NotFound(user)
    if BALANCES[user] < amount:
        raise InsufficientFunds(f"{user} has {BALANCES[user]}, needs {amount}")
    BALANCES[user] -= amount
    return BALANCES[user]


# --- 2. the boundary: the ONLY place exceptions become responses --------------------------------
def endpoint(fn) -> tuple[int, dict]:
    try:
        return 200, {"result": fn()}
    except AppError as e:
        print(f"  [log] {type(e).__name__}: {e}")                  # internal detail goes to logs
        return e.status, {"error": e.public_message}              # user sees the safe message only
    except Exception as e:                                         # unknown bug: log it, hide it
        print(f"  [log] UNHANDLED {type(e).__name__}: {e}")
        return 500, {"error": AppError.public_message}


if __name__ == "__main__":
    print(endpoint(lambda: withdraw("alice", 20)))
    print(endpoint(lambda: withdraw("alice", 999)))
    print(endpoint(lambda: withdraw("bob", 1)))
    print(endpoint(lambda: 1 / 0))

    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("503")
        return "ok"

    result = retry(flaky)
    print("retry succeeded after", calls["n"] - 1, "failures ->", result)

    print("\nRules: fail fast on bad input/config, retry only transient + idempotent calls, never `except: pass`,")
    print("never leak stack traces or SQL to users, log once at the boundary (not at every layer).")
