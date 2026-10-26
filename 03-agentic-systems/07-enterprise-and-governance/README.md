# 03 · Agentic Systems › Enterprise architecture & AI governance

> What an enterprise will ask before letting your agent near real systems and real data. Awareness
> level: know the vocabulary, know the building blocks, be able to sketch each one.

**Budget:** ~2–3 days · Domain checklist: [../README.md](../README.md)

---

## The one idea

An enterprise agent is a normal backend system plus three things a demo doesn't have:

1. **A control plane**: one place that decides who/what an agent is, what it may touch, and what it costs.
2. **Evidence**: a trail that proves what the agent did and why, to someone who wasn't there.
3. **Accountability**: a named owner, a risk tier, and a human for the risky parts.

**Architecture** is how you build 1. **Governance** is how you produce 2 and 3.

## The order (and why)

| # | Topic | Why it comes here | Time |
|---|---|---|---|
| 01 | [Enterprise agent architecture](01-enterprise-agent-architecture/) | The map: layers and where controls plug in. | 0.5 d |
| 02 | [Identity & access](02-identity-and-access/) | Every control starts with "who is acting?" | 0.5 d |
| 03 | [Policy & guardrails](03-policy-and-guardrails/) | Turning "who" into allow / deny / ask a human. | 0.5 d |
| 04 | [Audit & accountability](04-audit-and-accountability/) | Proving what happened afterwards. | 0.5 d |
| 05 | [Risk & regulation](05-risk-and-regulation/) | The external frameworks the above satisfies. | 0.5 d |

Every topic has a `README.md` (notes) and a `practice/` script. Scripts are offline, stdlib only:

```bash
python 01-enterprise-agent-architecture/practice/tool_gateway.py
python 02-identity-and-access/practice/delegated_tokens.py
python 03-policy-and-guardrails/practice/policy_engine.py
python 04-audit-and-accountability/practice/audit_log.py
python 05-risk-and-regulation/practice/risk_tiering.py
```

## FDE angle

In a customer deployment the security/compliance review is often the real gate, not the model quality.
Arriving with answers ("agents get scoped, short-lived credentials; every call is logged; writes in
prod need approval") turns a 3-month review into a 3-week one.

## Done with this section when

You can explain, without notes: what a tool gateway is, why an agent should never hold the user's
own credentials, what "default deny" means, what goes in an agent audit record, and which risk tier a
hiring-screening agent falls into.
