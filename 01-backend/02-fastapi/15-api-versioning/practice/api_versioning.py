"""API versioning: change your API without breaking clients who already depend on it.

Safe (non-breaking) changes need NO new version: add an endpoint, add an optional request field,
add a response field. Breaking changes (rename/remove a field, change a type or meaning, make
something required) need a new version, with the old one kept alive and deprecated on a schedule.

Strategy shown: URL prefix (/v1, /v2): most common, visible, easy to route and cache.
Alternative: header (Accept: application/vnd.api.v2+json): cleaner URLs, harder to test/debug.

Needs: pip install fastapi httpx      Run:  python api_versioning.py
"""

from fastapi import APIRouter, FastAPI, Response
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()
USERS = {1: {"first": "Ana", "last": "Silva", "email": "ana@x.com"}}


# ---- v1: the original contract. Frozen. Clients depend on `name`. ----
class UserV1(BaseModel):
    id: int
    name: str


v1 = APIRouter(prefix="/v1", tags=["v1"])


@v1.get("/users/{uid}", response_model=UserV1, deprecated=True)      # shows as struck-through in Swagger
def get_user_v1(uid: int, response: Response):
    u = USERS[uid]
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Sat, 31 Oct 2027 23:59:59 GMT"     # date v1 will stop working
    response.headers["Link"] = '</v2/users/1>; rel="successor-version"'
    return {"id": uid, "name": f"{u['first']} {u['last']}"}


# ---- v2: breaking change (name split into first/last). Shares the same business logic. ----
class UserV2(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str                                                         # new field: additive, fine on its own


v2 = APIRouter(prefix="/v2", tags=["v2"])


@v2.get("/users/{uid}", response_model=UserV2)
def get_user_v2(uid: int):
    u = USERS[uid]
    return {"id": uid, "first_name": u["first"], "last_name": u["last"], "email": u["email"]}


app.include_router(v1)
app.include_router(v2)

if __name__ == "__main__":
    c = TestClient(app)
    r1 = c.get("/v1/users/1")
    print("v1:", r1.json())
    print("    headers:", {k: v for k, v in r1.headers.items() if k in ("deprecation", "sunset", "link")})
    print("v2:", c.get("/v2/users/1").json())
    paths = c.get("/openapi.json").json()["paths"]
    print("v1 flagged deprecated in OpenAPI:", paths["/v1/users/{uid}"]["get"].get("deprecated"))

    print("""
Checklist for a breaking change:
  1. Prefer additive changes so you never need v2.   2. Ship v2 next to v1 (share services, only schemas differ).
  3. Announce + set Deprecation/Sunset headers.        4. Watch v1 traffic per client (logs) and message them.
  5. Remove v1 only after the sunset date and when traffic is ~0.
Keep versions few: every live version is code you must test, secure and support.""")
