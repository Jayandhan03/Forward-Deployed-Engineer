"""Cookies and sessions: why you sign (or store server-side) session data, and the flags that matter.

Two designs:
  - server-side session: cookie holds a random id; data lives in your store (easy to revoke)
  - signed cookie: cookie holds the data + an HMAC signature (no store, harder to revoke)

Run:
    python signed_session.py
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

SECRET = b"demo-only-load-from-a-secret-manager"


def sign_cookie(data: dict, ttl_s: int = 3600) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({**data, "exp": time.time() + ttl_s}).encode()).decode()
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def read_cookie(cookie: str) -> dict | None:
    try:
        payload, sig = cookie.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):                 # constant-time compare
        return None
    data = json.loads(base64.urlsafe_b64decode(payload))
    return data if data["exp"] > time.time() else None


SESSIONS: dict[str, dict] = {}                                 # stand-in for Redis


def create_server_session(data: dict) -> str:
    sid = secrets.token_urlsafe(32)                            # unguessable, never user-derived
    SESSIONS[sid] = data
    return sid


def set_cookie_header(name: str, value: str) -> str:
    """Flags that make cookies safer. Know what each one stops."""
    return (f"Set-Cookie: {name}={value}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600")


if __name__ == "__main__":
    c = sign_cookie({"user": "alice", "role": "member"})
    print("signed cookie reads back:", read_cookie(c))

    payload, sig = c.rsplit(".", 1)
    tampered = base64.urlsafe_b64encode(json.dumps({"user": "alice", "role": "admin", "exp": 9e12}).encode()).decode()
    print("tampered role=admin     :", read_cookie(f"{tampered}.{sig}"), "(signature mismatch)")
    print("expired cookie          :", read_cookie(sign_cookie({"user": "alice"}, ttl_s=-1)))

    sid = create_server_session({"user": "alice"})
    print("\nserver-side session id  :", sid[:16] + "...", "->", SESSIONS[sid])
    del SESSIONS[sid]
    print("after logout/revoke     :", SESSIONS.get(sid), "(instantly invalid, the big advantage)")

    print("\n" + set_cookie_header("sid", sid[:12] + "..."))
    print("HttpOnly: JS can't read it (limits XSS theft) | Secure: HTTPS only | SameSite: limits CSRF")
    print("Note a signed cookie is signed, NOT encrypted: anyone can read it, nobody can alter it.")
