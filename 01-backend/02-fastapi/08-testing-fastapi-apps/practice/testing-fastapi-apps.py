"""Testing FastAPI apps: TestClient + dependency overrides + a fresh state per test.

Written as pytest-style `test_*` functions with plain asserts, so it runs both ways:
    python testing-fastapi-apps.py          (built-in mini runner below, no pytest needed)
    pytest testing-fastapi-apps.py          (when pytest is installed)

Needs: pip install fastapi httpx
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ---------------- the app under test (normally: from app.main import app) ----------------
app = FastAPI()


class Repo:
    """Stands in for the DB. Real projects: a SQLAlchemy session per test, rolled back after."""

    def __init__(self):
        self.todos: dict[int, str] = {}

    def add(self, title: str) -> int:
        tid = len(self.todos) + 1
        self.todos[tid] = title
        return tid


_real_repo = Repo()


def get_repo() -> Repo:
    return _real_repo


class TodoIn(BaseModel):
    title: str


@app.post("/todos", status_code=201)
def create(body: TodoIn, repo: Annotated[Repo, Depends(get_repo)]):
    return {"id": repo.add(body.title), "title": body.title}


@app.get("/todos/{tid}")
def read(tid: int, repo: Annotated[Repo, Depends(get_repo)]):
    if tid not in repo.todos:
        raise HTTPException(404, "not found")
    return {"id": tid, "title": repo.todos[tid]}


# ---------------- fixtures (pytest: @pytest.fixture) ----------------
def make_client() -> tuple[TestClient, Repo]:
    repo = Repo()                                          # fresh, isolated state => tests can't affect each other
    app.dependency_overrides[get_repo] = lambda: repo      # swap the real dependency
    return TestClient(app), repo


# ---------------- tests: arrange / act / assert ----------------
def test_create_returns_201_and_stores():
    client, repo = make_client()
    r = client.post("/todos", json={"title": "ship it"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "title": "ship it"}
    assert repo.todos == {1: "ship it"}


def test_read_missing_is_404():
    client, _ = make_client()
    assert client.get("/todos/99").status_code == 404


def test_validation_error_is_422():
    client, _ = make_client()
    assert client.post("/todos", json={"wrong": 1}).status_code == 422


def test_isolation_state_does_not_leak():
    client, repo = make_client()
    assert repo.todos == {}                                # previous tests' data is gone


# ---------------- tiny runner (pytest does this for you) ----------------
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError as e:
            print("FAIL", t.__name__, e)
        finally:
            app.dependency_overrides.clear()
    print("\nTest pyramid: many fast unit tests (services) > some API tests like these > few end-to-end.")
    print("Test the contract: status code, body shape, side effects, and the unhappy paths (404, 422, 401).")
    print("Async handlers/DB: use httpx.AsyncClient + pytest-asyncio. Real DB: a transaction rolled back per test.")
