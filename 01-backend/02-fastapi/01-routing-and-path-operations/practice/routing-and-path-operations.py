"""Routing & path operations: map method + path to a function; params come from where you declare them.

FastAPI decides where each argument comes from by its declaration:
  name in the path "/items/{item_id}"  -> path param
  plain type (int, str, bool)           -> query param (?limit=5)
  Header(...) / Cookie(...)             -> header / cookie
  pydantic model                        -> JSON body (next topic)

Needs: pip install fastapi httpx      Run:  python routing-and-path-operations.py
"""

import asyncio

from fastapi import APIRouter, FastAPI, Header, status
from fastapi.testclient import TestClient

app = FastAPI()
router = APIRouter(prefix="/items", tags=["items"])          # prefix + tags apply to every route in it
DB = {1: "pen", 2: "book"}


def _on_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


@router.get("/{item_id}")                                     # path param, validated as int
def get_item(item_id: int, verbose: bool = False, x_trace: str | None = Header(None)):
    return {"id": item_id, "name": DB.get(item_id), "verbose": verbose, "trace": x_trace}


@router.get("")
def list_items(limit: int = 10, q: str | None = None):        # query params with defaults = optional
    return {"limit": limit, "q": q, "items": list(DB.values())[:limit]}


@router.post("", status_code=status.HTTP_201_CREATED)         # choose the success code explicitly
def create_item(name: str):
    DB[len(DB) + 1] = name
    return {"created": name}


@router.get("/slow/sync")
def sync_handler():                                           # plain def -> runs in a thread pool
    return {"on_event_loop": _on_loop()}


@router.get("/slow/async")
async def async_handler():                                    # async def -> runs ON the event loop
    await asyncio.sleep(0)                                    # never call blocking code (requests, time.sleep) here
    return {"on_event_loop": _on_loop()}


app.include_router(router)

if __name__ == "__main__":
    c = TestClient(app)
    print(c.get("/items/1?verbose=true", headers={"X-Trace": "abc"}).json())
    print(c.get("/items/abc").status_code, "<- 'abc' is not an int: automatic 422")
    print(c.get("/items?limit=1&q=pen").json())
    r = c.post("/items?name=lamp")
    print(r.status_code, r.json())
    print("sync  def handler:", c.get("/items/slow/sync").json())
    print("async def handler:", c.get("/items/slow/async").json())
    print("\nSwagger UI is free at /docs. Route order matters: declare /items/me BEFORE /items/{id}.")
