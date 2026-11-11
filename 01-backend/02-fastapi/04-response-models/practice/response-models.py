"""Response models: declare what leaves the API; FastAPI filters and documents it.

Return a DB object with `password_hash` on it and, with response_model=UserOut, the hash is dropped.
Separate In / DB / Out models are the standard pattern: never reuse the input model as output.

Needs: pip install fastapi httpx      Run:  python response-models.py
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

app = FastAPI()


class UserIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)          # allow building from ORM objects, not only dicts
    id: int
    email: str
    nickname: str | None = None
    created_at: datetime


class UserRow:                                               # stands in for a SQLAlchemy row
    def __init__(self, id, email, password_hash):
        self.id, self.email, self.password_hash = id, email, password_hash
        self.nickname, self.created_at = None, datetime(2026, 11, 11, 9, 0)


@app.post("/users", response_model=UserOut, status_code=201)
def create(user: UserIn):
    return UserRow(1, user.email, "argon2$secret-hash")      # extra attrs (password_hash) are filtered out


@app.get("/users/{uid}", response_model=UserOut, response_model_exclude_none=True)   # hide null fields
def get(uid: int):
    return UserRow(uid, "a@x.com", "argon2$secret-hash")


@app.get("/users", response_model=list[UserOut])             # collections work too
def all_users():
    return [UserRow(1, "a@x.com", "h"), UserRow(2, "b@x.com", "h")]


if __name__ == "__main__":
    c = TestClient(app)
    r = c.post("/users", json={"email": "a@x.com", "password": "hunter2"})
    print(r.status_code, r.json(), "<- no password_hash, datetime became ISO string")
    print("exclude_none:", c.get("/users/7").json())
    print("list        :", [u["email"] for u in c.get("/users").json()])
    print("\nWhy: (1) leak protection, (2) response shape in OpenAPI docs + generated clients, (3) serialization.")
    print("Pattern: UserIn (input) / UserOut (public) / DB model (internal). Fields you don't list never leave.")
