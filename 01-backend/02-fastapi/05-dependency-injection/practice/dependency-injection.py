"""Dependency injection: declare what a handler needs with Depends(); FastAPI builds and passes it.

Use it for: DB sessions, current user, settings, pagination params, permission checks.
`yield` dependencies give setup + cleanup. `dependency_overrides` swaps them in tests: the payoff.

Needs: pip install fastapi httpx      Run:  python dependency-injection.py
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()
events: list[str] = []


# 1. a resource with setup/cleanup (think: DB session). Cleanup runs after the response, even on error.
class FakeDB:
    def __init__(self):
        self.users = {"t-123": "ana"}


def get_db():
    events.append("open db")
    db = FakeDB()
    try:
        yield db
    finally:
        events.append("close db")


# 2. a dependency that depends on another dependency (chains are resolved automatically)
def current_user(db: Annotated[FakeDB, Depends(get_db)], authorization: str = Header(default="")) -> str:
    user = db.users.get(authorization.removeprefix("Bearer "))
    if not user:
        raise HTTPException(401, "invalid token")
    return user


# 3. a parametrised dependency (factory) for permissions
def require_role(role: str):
    def check(user: Annotated[str, Depends(current_user)]):
        if role != "admin" or user != "ana":
            raise HTTPException(403, "forbidden")
        return user
    return check


# 4. reusable shared params
def pagination(limit: int = 10, offset: int = 0) -> dict:
    return {"limit": min(limit, 100), "offset": offset}       # clamp once, for every list endpoint


DB = Annotated[FakeDB, Depends(get_db)]                      # alias: keeps signatures short
User = Annotated[str, Depends(current_user)]


@app.get("/me")
def me(user: User):
    return {"user": user}


@app.get("/items")
def items(page: Annotated[dict, Depends(pagination)], user: User):
    return {"user": user, **page}


@app.delete("/admin/purge")
def purge(user: Annotated[str, Depends(require_role("admin"))]):
    return {"purged_by": user}


if __name__ == "__main__":
    c = TestClient(app)
    h = {"Authorization": "Bearer t-123"}
    print(c.get("/me", headers=h).json(), "| events:", events)
    print(c.get("/me").status_code, "<- no token -> 401")
    print(c.get("/items?limit=9999", headers=h).json(), "<- limit clamped")
    print(c.delete("/admin/purge", headers=h).json())

    # The payoff: replace the real dependency in a test, no real DB or token needed.
    app.dependency_overrides[current_user] = lambda: "test-user"
    print("overridden:", c.get("/me").json())
    app.dependency_overrides.clear()

    print("\nWhy: handlers stay tiny, logic is reusable, and tests swap dependencies instead of patching globals.")
