"""Sessions vs tokens: where the state lives decides how you revoke.

Session: opaque id, state on the server -> revoke instantly, needs a shared store.
Stateless token (JWT-style): signed claims, no lookup -> scales easily, valid until it expires.
Common compromise: short-lived access token + revocable refresh token.

Run:
    python sessions_vs_tokens.py
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

SECRET = b"demo-only-use-a-secret-manager"
SESSIONS: dict[str, dict] = {}
REVOKED_REFRESH: set[str] = set()


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_token(claims: dict, ttl_s: float) -> str:
    body = b64(json.dumps({**claims, "exp": time.time() + ttl_s}).encode())
    return f"{body}.{b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())}"


def verify_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".")
    except ValueError:
        return None
    good = b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, good):
        return None
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    return claims if claims["exp"] > time.time() else None


if __name__ == "__main__":
    print("1. server-side session")
    sid = secrets.token_urlsafe(24)
    SESSIONS[sid] = {"user": "alice"}
    print("   valid     :", SESSIONS.get(sid))
    del SESSIONS[sid]
    print("   revoked   :", SESSIONS.get(sid), "<- effective immediately")

    print("\n2. stateless token")
    token = issue_token({"user": "alice"}, ttl_s=60)
    print("   valid     :", verify_token(token))
    print("   'revoked' :", verify_token(token), "<- nothing to delete, still valid until exp")
    forged = token.split(".")[0] + "." + b64(b"x" * 32)
    print("   forged    :", verify_token(forged))
    print("   expired   :", verify_token(issue_token({"user": "alice"}, ttl_s=-1)))

    print("\n3. access + refresh pair")
    access = issue_token({"user": "alice", "type": "access"}, ttl_s=300)
    refresh = issue_token({"user": "alice", "type": "refresh", "jti": secrets.token_hex(4)}, ttl_s=86400)
    jti = verify_token(refresh)["jti"]
    REVOKED_REFRESH.add(jti)
    print("   access still works for up to 5 min :", verify_token(access) is not None)
    print("   refresh after revoke -> new access :", "denied" if jti in REVOKED_REFRESH else "allowed")

    print("\nPick sessions for simple web apps and easy revocation; short-lived tokens for APIs and")
    print("service-to-service calls. Never put secrets in claims: they are signed, not encrypted.")
