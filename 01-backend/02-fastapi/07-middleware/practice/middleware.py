"""Middleware: code that wraps EVERY request (before the handler, and after it).

Typical jobs: request ID, timing, logging, security headers, CORS, auth gates, gzip.
Order matters: the middleware added LAST is the OUTERMOST layer (runs first on the way in).

Needs: pip install fastapi httpx      Run:  python middleware.py
"""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()
trace: list[str] = []


@app.middleware("http")
async def request_id_and_timing(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:8]    # honour an upstream ID if present
    request.state.request_id = rid                                       # handlers can read it
    trace.append("timing: in")
    start = time.perf_counter()
    response = await call_next(request)                                  # <- the rest of the app runs here
    ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = rid
    response.headers["X-Process-Time-ms"] = f"{ms:.2f}"
    trace.append("timing: out")
    return response


@app.middleware("http")                                                  # added second => runs FIRST
async def api_key_gate(request: Request, call_next):
    trace.append("auth: in")
    if request.url.path.startswith("/private") and request.headers.get("x-api-key") != "k-123":
        return JSONResponse({"error": "missing or bad API key"}, status_code=401)   # short-circuit: handler never runs
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"               # security header on every response
    return response


app.add_middleware(CORSMiddleware, allow_origins=["https://app.example.com"], allow_methods=["*"], allow_headers=["*"])


@app.get("/public")
def public(request: Request):
    trace.append("handler")
    return {"request_id": request.state.request_id}


@app.get("/private/data")
def private():
    return {"secret": 42}


if __name__ == "__main__":
    c = TestClient(app)
    r = c.get("/public", headers={"X-Request-ID": "abc123"})
    print(r.json(), {k: v for k, v in r.headers.items() if k.startswith("x-")})
    print("order of execution:", trace)
    print("private, no key :", c.get("/private/data").status_code)
    print("private, key    :", c.get("/private/data", headers={"X-API-Key": "k-123"}).status_code)
    pre = c.options("/public", headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"})
    print("CORS preflight  :", pre.status_code, pre.headers.get("access-control-allow-origin"))
    print("\nUse middleware for cross-cutting concerns; use Depends() for per-route logic (auth user, DB).")
    print("Keep it fast and never read the whole body here: it breaks streaming. Heavy work belongs in the handler.")
