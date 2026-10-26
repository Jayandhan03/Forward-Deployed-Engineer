# Identity & access for agents

> An agent is a new kind of principal. Give it its own identity, act on behalf of a user, and hand it
> the smallest possible, shortest-lived permission.

**Practice:** [`practice/delegated_tokens.py`](practice/delegated_tokens.py)

## 1. The problem

Easy and wrong: give the agent one powerful service account (or the user's password) and hope the
prompt keeps it in line. A prompt-injected agent then has the *full* power of that account.

## 2. The rules

| Rule | Meaning |
|---|---|
| **Agent has its own identity** | Logs say `support-agent-v2 acting for alice`, not just `alice` or `service-account-1`. |
| **On-behalf-of (delegation)** | The agent's access = what the agent is allowed **∩** what the user is allowed. Never more than the user. |
| **Least privilege** | Scopes per task (`invoices:read`), not per system (`admin`). |
| **Short-lived credentials** | Minutes, not months. A leaked token expires on its own. |
| **Narrow on delegation** | A sub-agent gets a subset of its parent's scopes, never more. |
| **Secrets stay out of the model** | The model never sees API keys; the tool gateway attaches them at call time. |
| **Separate identities per environment** | Dev agents can't touch prod. |

## 3. How it looks in practice

```
User logs in (SSO / OIDC)
  -> platform issues a token: {agent, on_behalf_of: alice, scopes: [crm:read], exp: +5min}
  -> agent calls the tool gateway with that token
  -> gateway verifies signature, expiry, scope, then calls the real system
```

Real systems use OAuth 2.0 / OIDC, token exchange (RFC 8693) for on-behalf-of, and a vault or cloud
KMS for secrets. The script shows the idea with HMAC-signed tokens so it runs offline.

## 4. Worth knowing

- **Confused deputy:** an agent with broad power gets tricked by untrusted content into using it for
  someone else. Scoped, per-user tokens are the fix.
- **Human vs non-human identity:** agents are non-human identities. Many enterprises already track
  these (service accounts); agents need to join that inventory with an owner.
- **Revocation:** you need a way to kill one agent's access instantly (kill switch), not just wait for expiry.

## Try it

```bash
python practice/delegated_tokens.py
```

Watch four things fail safely: over-asking for scopes, sub-agent escalation, a forged token, an expired token.
