# Projects — the build ladder

Increasing difficulty. **Each project teaches one or two new concepts** — don't try to learn
everything in one build. Every project gets its own folder here with a real README (goal, new
concepts, build log, decisions, demo link) and, once it's non‑trivial, its own git branch and
eventually its own repo linked back here.

| # | Project | New concepts it forces you to learn | Leans on |
|---|---|---|---|
| 01 | **Notes API** | REST design, Pydantic models, Postgres + SQLAlchemy, Alembic, pytest | `01/00–04` |
| 02 | **Authentication service** | Password hashing, JWT access + refresh rotation, OAuth (Google/GitHub), RBAC | `01/06`, `07/02` |
| 03 | **URL shortener** | Redis caching, rate limiting, short‑code generation, analytics counters, cursor pagination | `01/05`, `06/00` |
| 04 | **Blog CMS** | Rich relations, full‑text search, image uploads to S3 + presigned URLs, drafts/publish workflow | `01/03`, `01/07` |
| 05 | **Chat application** | WebSockets, presence, pub/sub fan‑out, message ordering, backpressure | `01/02`, `01/05` |
| 06 | **File storage service** | Multipart/streamed uploads, S3, CDN, virus‑scan hook, quotas, background processing | `01/07`, `01/08` |
| 07 | **AI chat backend** | LLM provider abstraction, token streaming (SSE), conversation history, tool calling, cost logging | `02/00–01` |
| 08 | **RAG API** | Ingestion pipeline, chunking, pgvector/Qdrant, hybrid retrieval, reranking, citations, eval suite in CI | `02/02–04` |
| 09 | **Multi‑agent backend** | Agent loop, orchestration, queue‑backed workers, tracing, budgets, human‑in‑the‑loop | `03/*` |
| 10 | **SaaS backend** | Multi‑tenancy, organizations & roles, billing (Stripe), notifications, audit log, webhooks | `01/*`, `06/*`, `07/*` |
| 11 | **AI workspace (your Leora backend)** | Everything above, integrated: auth + orgs + RAG + agents + billing + observability, deployed | all domains |

## Rules

1. **Ship it deployed.** A project isn't done until it's running somewhere with HTTPS and a health check.
2. **Real README per project** — what, why, how to run, architecture sketch, decisions & trade‑offs, demo link.
3. **Tests + CI** from project 02 onward — lint, type‑check, test on every push.
4. **One write‑up per project** in [`../proof-of-work/writeups/`](../proof-of-work/writeups/) — what was hard, what you'd do differently.
5. **Post it** — a thread or a short video walkthrough on X, linked from the project README.

## Definition of done (per project)

- [ ] Deployed, HTTPS, health check, seeded demo data
- [ ] `README.md` with architecture sketch + decisions
- [ ] CI green (lint + types + tests)
- [ ] Structured logging + error tracking wired
- [ ] Security pass — every relevant `07-security/` item addressed
- [ ] Write‑up published + posted
