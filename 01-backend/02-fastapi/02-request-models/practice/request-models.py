"""Request models: a Pydantic class describes the JSON body; FastAPI parses + validates it for you.

You get: parsing, type coercion, nested objects, a 422 with exact error locations, and docs.
`Annotated[...]` is the modern way to attach metadata (Query/Body/Depends) to a parameter.

Needs: pip install fastapi httpx      Run:  python request-models.py
"""

from typing import Annotated

from fastapi import Body, FastAPI, Form, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()


class Address(BaseModel):
    city: str
    zip: str


class UserIn(BaseModel):
    name: str
    age: int
    address: Address                      # nested model -> nested JSON
    tags: list[str] = []                  # default => optional


@app.post("/users")
def create_user(user: UserIn):            # a single model param = the whole JSON body
    return {"name": user.name, "city": user.address.city, "age_type": type(user.age).__name__}


@app.post("/orders")
def create_order(
    user: UserIn,
    note: Annotated[str, Body()],                       # 2+ body params -> body must be {"user": {...}, "note": "..."}
    priority: Annotated[int, Query(ge=1, le=5)] = 3,    # simple types stay in the query string
):
    return {"user": user.name, "note": note, "priority": priority}


@app.post("/login")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):   # HTML form body
    return {"user": username}                           # needs `python-multipart` installed


if __name__ == "__main__":
    c = TestClient(app)
    good = {"name": "Ana", "age": "31", "address": {"city": "Oslo", "zip": "0150"}}
    print("1. coerces '31' -> int :", c.post("/users", json=good).json())

    bad = {"name": "Ana", "age": "old", "address": {"city": "Oslo"}}
    r = c.post("/users", json=bad)
    print("2. invalid ->", r.status_code)
    for e in r.json()["detail"]:
        print("    ", e["loc"], "|", e["msg"])

    print("3. multi-body :", c.post("/orders?priority=2", json={"user": good, "note": "gift"}).json())
    print("4. query bound:", c.post("/orders?priority=9", json={"user": good, "note": "x"}).status_code)
    print("\nRule: models for bodies, plain params for query/path, Form() only for HTML forms / OAuth2 login.")
