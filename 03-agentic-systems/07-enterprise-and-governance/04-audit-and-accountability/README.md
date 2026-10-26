# Audit & accountability

> When something goes wrong (or an auditor asks), you must be able to reconstruct who did what, with
> which model and prompt, and who approved it.

**Practice:** [`practice/audit_log.py`](practice/audit_log.py)
**Related:** [`../../04-observability/01-tracing-agent-runs`](../../04-observability/01-tracing-agent-runs/)

## 1. Tracing vs audit

| | Observability trace | Audit log |
|---|---|---|
| Audience | engineers debugging | auditors, security, legal |
| Question | "why was it slow / wrong?" | "who did what, and was it allowed?" |
| Retention | days to weeks | months to years (per policy) |
| Integrity | best-effort | tamper-evident, append-only |
| Content | everything useful, sampled | decisions and actions, complete |

Often the same pipeline feeds both, but they have different guarantees.

## 2. What an agent audit record contains

- **Who:** agent id + version, the user it acted for, tenant
- **What:** tool, arguments (with PII redacted or hashed), result summary
- **Decision:** allowed / denied / sent to approval, **which policy rule** decided, who approved
- **Reproducibility:** model id + version, prompt version, run id (links to the full trace)
- **When:** timestamp

Log **denials** as well as successes. A string of denied calls is how you spot an attack or a broken agent.

## 3. Tamper evidence

Each record stores the hash of the previous one, so editing history breaks the chain from that point
on. In production, add append-only storage (object lock / WORM) and periodically anchor the latest
hash somewhere the writers can't reach.

## 4. Accountability beyond logs

| Practice | What it is |
|---|---|
| **Agent registry with an owner** | Every agent has a named human/team responsible for it. |
| **Versioning** | Prompts, tools, policies and model choices are versioned. "What changed?" has an answer. |
| **Change control** | Prompt or tool changes go through review + evals, like code. |
| **Model cards / system docs** | Short doc: purpose, data, limits, known failure modes, eval results. |
| **Incident process** | Kill switch, how to roll back, who gets paged, post-mortem. |
| **Data lifecycle** | Retention limits, and deletion on request (GDPR) reaching memory and vector stores too. |

## 5. Privacy tension

Audit logs want detail; privacy law wants less personal data. Resolve by logging references and hashes
instead of raw content, redacting before logging, and setting retention per data class.

## Try it

```bash
python practice/audit_log.py
```
