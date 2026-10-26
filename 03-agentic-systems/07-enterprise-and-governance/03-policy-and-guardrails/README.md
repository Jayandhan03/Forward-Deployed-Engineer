# Policy & guardrails

> Prompts are suggestions. Policy is enforcement. Put the rules in code that runs outside the model.

**Practice:** [`practice/policy_engine.py`](practice/policy_engine.py)
**Related:** [`../../03-reliability/01-guardrails-and-validation`](../../03-reliability/01-guardrails-and-validation/), [`../../02-human-in-the-loop/01-approval-gates`](../../02-human-in-the-loop/01-approval-gates/)

## 1. Why not just put it in the system prompt?

A model can be talked out of its instructions (prompt injection, jailbreaks, plain error). So anything
that *must* hold, such as "never refund over $500" or "never email outside the company", is enforced in
code at the tool gateway, where the model can't argue with it.

## 2. Policy as code

Rules are data: `if (risk, environment, context) then allow | deny | require_approval`.

- **Default deny.** Anything no rule covers is blocked.
- **Reviewable.** Security and compliance can read and change rules without touching agent code
  (tools like Open Policy Agent exist for this at scale).
- **Versioned and tested** like any other code.

## 3. Classify actions by risk

| Class | Examples | Typical policy |
|---|---|---|
| Read | search docs, get record | allow (log it) |
| Write, reversible | update ticket, draft email | allow in dev; approve in prod |
| Write, irreversible / external | send email, move money, delete | human approval |
| Unknown | tool not in the registry | deny |

## 4. The guardrail set to know

| Guardrail | Stops | Where |
|---|---|---|
| Input checks | injection attempts, off-topic, secrets pasted in | before the model |
| **PII redaction** | personal data reaching models, logs, vendors | model gateway + logging |
| Output validation | malformed or unsafe output (schema, allow-lists) | after the model |
| **Taint tracking** | untrusted content (web, email, uploads) triggering privileged actions | tool gateway |
| Spend and step limits | runaway loops and bills | runtime |
| Approval gates | irreversible actions | tool gateway |

**Taint tracking** is the one worth remembering: once untrusted text has entered the context, treat
every write the agent attempts as possibly attacker-influenced and require a human. The script shows
the rule: `write + tainted → approve`.

## 5. Honest limits

No guardrail catches everything, especially classifier-based ones. Defence in depth: least privilege
(topic 02) means a fooled agent can still only do little damage; policy limits what it can try;
approvals cover the rest.

## Try it

```bash
python practice/policy_engine.py
```
