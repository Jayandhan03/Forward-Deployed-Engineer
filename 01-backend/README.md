# 01 · Backend

The spine. Every other domain — AI, agents, frontend, deploy — leans on this. **Go deep here.**

**Depth target:** L4–5. You should be able to build any backend for any AI product from an empty folder.
**Budget:** 8–10 weeks. **Core stack:** Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Redis, Docker.

> Rule: every concept below gets implemented in one of the `projects/` builds, not just read about.

---

## 00-http-foundations

You should be able to narrate exactly what happens between a button press and a rendered response.

- [ ] HTTP methods (safe/idempotent semantics) · [ ] Status codes (and which to actually return)
- [ ] Headers (content negotiation, caching, auth) · [ ] Cookies & sessions
- [ ] CORS — the preflight, the headers, why it bites · [ ] REST principles (and their limits)
- [ ] JSON & serialization · [ ] Request/response lifecycle end to end

## 01-python-app-skills

- [ ] Structured logging (JSON logs, correlation IDs, log levels)
- [ ] Configuration & settings (env‑based, `pydantic-settings`, 12‑factor)
- [ ] Error‑handling patterns (error types, boundaries, user‑safe messages)
- [ ] Project layout (routers / services / repositories / schemas / domain)
- [ ] Dependency & env management (`uv`/`poetry`, lockfiles, reproducible builds)

## 02-fastapi — master it

- [ ] Routing & path operations · [ ] Request models · [ ] Response models
- [ ] **Dependency injection** — and why it makes handlers testable
- [ ] Validation with Pydantic (v2: validators, `model_config`, custom types)
- [ ] File uploads — images, PDFs, audio; size limits, streaming to storage
- [ ] Streaming responses — SSE and chunked; the backbone of LLM UIs
- [ ] Background tasks · [ ] Middleware · [ ] Exception handlers
- [ ] Rate limiting · [ ] Pagination (offset vs cursor) · [ ] API versioning
- [ ] OpenAPI & Swagger — and generating a typed frontend client from it
- [ ] WebSockets · [ ] Testing FastAPI apps (`TestClient`, `httpx`, fixtures, DB per test)

## 03-databases-sql — PostgreSQL

- [ ] Postgres basics — types, `psql`, `\d` · [ ] Schema design & normalization (and when to denormalize)
- [ ] Joins · [ ] Indexes (B‑tree, partial, composite, covering; when they're ignored)
- [ ] Transactions & isolation levels — read‑committed vs repeatable‑read, deadlocks
- [ ] Constraints & views · [ ] `EXPLAIN ANALYZE` & query tuning

## 04-orm-sqlalchemy

- [ ] SQLAlchemy Core · [ ] ORM models & mappings (2.x style) · [ ] Session & unit of work
- [ ] Relationships & loading strategies (lazy / selectin / joined)
- [ ] **Alembic migrations** — autogenerate, review, downgrade, data migrations
- [ ] The N+1 query problem — spotting it, fixing it

## 05-redis

- [ ] Caching patterns (cache‑aside, write‑through, TTLs) · [ ] Session store
- [ ] Rate limiter (token bucket / sliding window in Redis) · [ ] Pub/sub
- [ ] Queues & streams · [ ] Cache invalidation strategies

## 06-auth

- [ ] Password hashing — bcrypt / argon2, never fast hashes
- [ ] JWT access tokens — claims, expiry, signing (HS vs RS)
- [ ] Refresh tokens & rotation — reuse detection, revocation
- [ ] OAuth2 — Google login · [ ] OAuth2 — GitHub login · [ ] API keys
- [ ] RBAC & permissions · [ ] Sessions vs tokens — the real trade‑offs

## 07-file-storage

- [ ] S3 upload & download (boto3 / `aioboto3`) · [ ] Presigned URLs (direct browser upload)
- [ ] CDN & edge caching · [ ] Image optimization · [ ] Streaming large files

## 08-async-and-workers

- [ ] Async database access (`asyncpg`, async SQLAlchemy) · [ ] Celery tasks · [ ] RQ (Redis Queue)
- [ ] Task scheduling & cron (Celery beat) · [ ] Idempotency & retries · [ ] Dead‑letter queues

## 09-production-backend

- [ ] Logging & log levels in prod · [ ] Metrics (Prometheus) · [ ] Distributed tracing (OpenTelemetry)
- [ ] Error tracking (Sentry) · [ ] Health & readiness checks · [ ] Graceful shutdown
- [ ] Secrets management · [ ] Load & stress testing (`locust`, `k6`)

---

## Projects for this domain

`projects/01` Notes API → `02` Auth service → `03` URL shortener → `04` Blog CMS →
`05` Chat app (WebSockets) → `06` File storage service. Then the AI backends in domains 02–03.

## Done when

You can stand up a new FastAPI service with auth, Postgres + migrations, Redis caching, background
workers, structured logs, health checks, and a test suite — from an empty folder, in an afternoon,
and explain every dependency you added.

## Resources

- FastAPI docs (cover‑to‑cover) · SQLAlchemy 2.0 docs · *Designing Data‑Intensive Applications* ch. 1–3, 7
- *Architecture Patterns with Python* (Percival & Gregory) — repository / unit‑of‑work / service layer
- *The Postgres docs* — indexes & `EXPLAIN` chapters · Redis docs — data types & patterns
