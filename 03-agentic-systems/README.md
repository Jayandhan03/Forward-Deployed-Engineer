# 03 · Agentic Systems

Production agentic AI, end to end. An agent system is a backend system (domain 01) with an LLM in the
control loop (domain 02) — plus the hard parts: it's stateful, long‑running, non‑deterministic, calls
tools that touch the real world, and can loop forever or burn money if you let it.

**Depth target:** L4–5 — this is your specialization. **Budget:** 4–5 weeks.
**Output of this domain:** a written, diagrammed reference architecture you could hand to another engineer.

---

## 00-agent-foundations

→ **Study order + topic folders:** [00-agent-foundations/README.md](00-agent-foundations/README.md)

- [ ] The agent loop — reason → act → observe → repeat; stop conditions
- [ ] Tool design — narrow, well‑described, safe‑by‑default; input/output schemas; errors as data
- [ ] Planning strategies — react vs plan‑then‑execute vs decomposition; when each fits
- [ ] Memory — short‑term (context) vs long‑term (store + retrieval); what to persist, what to forget
- [ ] Context & state management — assembling the window each turn; run state as a first‑class object

## 01-orchestration

→ **Study order + topic folders:** [01-orchestration/README.md](01-orchestration/README.md)

- [ ] Single‑agent workflow — one loop, a toolset, a budget
- [ ] Multi‑agent patterns — supervisor/worker, pipeline, debate; the cost of coordination
- [ ] Router & supervisor — classify intent, dispatch, aggregate
- [ ] Handoffs & delegation — passing state and responsibility cleanly
- [ ] Framework notes — LangGraph, Anthropic Agent SDK, others; what to adopt vs hand‑roll

## 02-human-in-the-loop

→ **Study order + topic folders:** [02-human-in-the-loop/README.md](02-human-in-the-loop/README.md)

- [ ] Approval gates — pause before irreversible/expensive actions
- [ ] Interrupts & resume — durable pause, external input, continue from state
- [ ] Review queues — surface agent actions for human sign‑off
- [ ] Feedback capture — thumbs / edits / corrections wired back into evals

## 03-reliability

→ **Study order + topic folders:** [03-reliability/README.md](03-reliability/README.md)

- [ ] Guardrails & output validation — schema checks, allow/deny lists, content filters
- [ ] Timeouts, retries, circuit breakers — per tool and per run
- [ ] Tool sandboxing & least privilege — scoped credentials, network egress limits, dry‑run mode
- [ ] Cost & budget limits — per run, per user, per day; hard stop
- [ ] Runaway‑loop protection — max steps, no‑progress detection, kill switch

## 04-observability

→ **Study order + topic folders:** [04-observability/README.md](04-observability/README.md)

- [ ] Tracing agent runs — one trace per run, spans per step/tool call
- [ ] Step & span logging — inputs, outputs, tokens, cost, latency at each hop
- [ ] Replay & debugging — reconstruct a run from its trace
- [ ] Agent eval harness — task suite with success criteria, run in CI and nightly
- [ ] Online monitoring & alerting — success rate, cost, latency, tool‑error rate

## 05-deployment

→ **Study order + topic folders:** [05-deployment/README.md](05-deployment/README.md)

- [ ] Stateful vs stateless agents — where run state lives
- [ ] Queue‑backed agent workers — enqueue run → worker executes → stream results out
- [ ] Streaming results to the client — SSE/WebSocket, partial output, cancel
- [ ] Session & run storage — schema for runs, steps, messages, artifacts
- [ ] Scaling agents — concurrency limits, provider rate limits, backpressure, cost ceilings

## 07-enterprise-and-governance

→ **Study order + topic folders:** [07-enterprise-and-governance/README.md](07-enterprise-and-governance/README.md)

- [ ] Enterprise agent architecture — gateways, registry, tenant isolation, MCP in the enterprise
- [ ] Identity & access — agent identity, on‑behalf‑of, least privilege, short‑lived scoped tokens
- [ ] Policy & guardrails — policy as code, risk‑classed actions, PII redaction, taint tracking
- [ ] Audit & accountability — tamper‑evident logs, versioning, owners, incident process
- [ ] Risk & regulation — EU AI Act tiers, NIST AI RMF, ISO 42001, go‑live checklist

## 06-reference-architecture

→ **Study order + topic folders:** [06-reference-architecture/README.md](06-reference-architecture/README.md)

The deliverable. Write these as real documents (Markdown + diagrams committed alongside):

- [ ] **End‑to‑end architecture** — API → queue → agent worker → tools → stores → streaming back
- [ ] **Data‑flow diagram** — request to response, every hop
- [ ] **Component inventory** — every service, store, and external dependency with its job
- [ ] **Tech choices & trade‑offs** — what you picked, what you rejected, why
- [ ] **Threat model** — prompt injection, tool abuse, data exfiltration, cost attacks
- [ ] **Cost model** — $/run breakdown, where it concentrates, how to cap it

---

## Projects for this domain

`projects/09` Multi‑agent backend, then fold everything into `projects/11` AI workspace (your Leora).

## Done when

You can whiteboard a production agent platform — queue, workers, tool sandbox, run store, tracing,
evals, budgets, human‑in‑the‑loop — name the failure modes, and say what each component costs.

## Resources

- Anthropic: "Building effective agents", tool‑use guide, prompt‑injection guidance.
- LangGraph docs (persistence, human‑in‑the‑loop, streaming) — even if you hand‑roll, the concepts transfer.
- OpenTelemetry for traces; an LLM‑observability tool (Langfuse / Phoenix / Braintrust) — pick one.
- Re‑read `06-system-design/03-distributed` and `04-resilience` with agents in mind.
