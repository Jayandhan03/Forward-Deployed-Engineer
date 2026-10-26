"""Agent credentials: short-lived, scoped, and never broader than the user who delegated.

Run:
    python delegated_tokens.py
"""

import base64
import hashlib
import hmac
import json
import time

SECRET = b"demo-only-use-a-KMS-or-vault-in-production"


def _sign(payload: bytes) -> str:
    return hmac.new(SECRET, payload, hashlib.sha256).hexdigest()


def issue(agent_id: str, user_id: str, user_scopes: set[str], requested: set[str],
          ttl_s: int = 300) -> str:
    """Token scopes = what the agent asked for AND what the user actually has."""
    granted = sorted(requested & user_scopes)
    claims = {"agent": agent_id, "on_behalf_of": user_id, "scopes": granted,
              "exp": time.time() + ttl_s}
    body = base64.urlsafe_b64encode(json.dumps(claims).encode())
    return f"{body.decode()}.{_sign(body)}"


def verify(token: str) -> dict:
    body, sig = token.split(".")
    if not hmac.compare_digest(sig, _sign(body.encode())):
        raise PermissionError("bad signature (token was tampered with)")
    claims = json.loads(base64.urlsafe_b64decode(body))
    if claims["exp"] < time.time():
        raise PermissionError("token expired")
    return claims


def delegate(token: str, sub_agent: str, scopes: set[str]) -> str:
    """A parent agent hands a sub-agent LESS power, never more."""
    parent = verify(token)
    narrowed = set(parent["scopes"]) & scopes
    return issue(sub_agent, parent["on_behalf_of"], set(parent["scopes"]), narrowed,
                 ttl_s=int(parent["exp"] - time.time()))


if __name__ == "__main__":
    alice_has = {"crm:read", "crm:write", "email:send"}

    tok = issue("sales-agent", "alice", alice_has, requested={"crm:read", "billing:admin"})
    print("1. asked for billing:admin, alice doesn't have it ->", verify(tok)["scopes"])

    sub = delegate(tok, "summarizer-subagent", {"crm:read", "crm:write"})
    print("2. sub-agent asked for crm:write, parent lacks it  ->", verify(sub)["scopes"])

    _, sig = tok.split(".")
    forged_body = base64.urlsafe_b64encode(json.dumps(
        {**verify(tok), "scopes": ["billing:admin"]}).encode()).decode()
    cases = [("3. forged token", f"{forged_body}.{sig}"),
             ("4. expired token", issue("a", "alice", alice_has, {"crm:read"}, ttl_s=-1))]
    for label, t in cases:
        try:
            verify(t)
        except PermissionError as e:
            print(f"{label:<17} -> rejected: {e}")
