# 06 · System Design & Architecture

Where "does it work" stops being enough and "does it survive scale, load, and failure" takes over.
The real senior skill here isn't memorizing patterns — it's **trade‑off thinking**: every choice
costs something, and the job is choosing which cost you can afford.

**Depth target:** L4, then revisit forever. **Budget:** 3–4 weeks focused, then one case study a week.

---

## 00-fundamentals

- [ ] API design — resources, versioning, pagination, errors, idempotency keys, contracts
- [ ] Back‑of‑the‑envelope estimation — QPS, storage, bandwidth, cost from first principles
- [ ] Latency numbers every engineer should know — memory vs SSD vs network vs cross‑region
- [ ] **Trade‑off thinking** — name the cost of every architectural choice, out loud

## 01-scaling

- [ ] Vertical vs horizontal — when each stops working
- [ ] Load balancing — L4 vs L7, algorithms, sticky sessions, health checks
- [ ] Replication — leader/follower, replication lag, read scaling
- [ ] Sharding & partitioning — key choice, hotspots, resharding pain
- [ ] Stateless services — push state to data stores so you can scale out

## 02-data

- [ ] SQL vs NoSQL selection — access patterns drive the choice, not hype
- [ ] Caching strategies — cache‑aside/read‑through/write‑through, stampede, TTL vs invalidation
- [ ] CDN — what to put at the edge, cache keys, purging
- [ ] Database scaling — read replicas, connection pooling, partitioning, when to add a cache
- [ ] Indexing at scale — write amplification, index bloat, covering indexes

## 03-distributed

- [ ] CAP theorem — and PACELC; what you actually give up during a partition
- [ ] Consistency models — strong, eventual, causal, read‑your‑writes
- [ ] Event‑driven architecture — decoupling via events; choreography vs orchestration
- [ ] Message queues — Kafka vs SQS vs RabbitMQ; ordering, partitioning, backpressure
- [ ] Idempotency & delivery guarantees — at‑least‑once is the default; design for duplicates
- [ ] Consensus basics — quorums, Raft at a conceptual level, why it's expensive

## 04-resilience

- [ ] Timeouts, retries, backoff — with jitter; retry budgets
- [ ] Circuit breakers — closed/open/half‑open, fallback paths
- [ ] Bulkheads & isolation — one slow dependency shouldn't sink the ship
- [ ] Graceful degradation — serve stale, serve partial, shed load
- [ ] Designing for failure — assume every dependency will be down; chaos thinking

## 05-architecture

- [ ] Monolith vs microservices — the real trade‑offs; why a small team should start monolith
- [ ] Service boundaries — along data ownership and rate of change
- [ ] API gateway — auth, rate limiting, routing at the edge
- [ ] Backend‑for‑frontend (BFF) — per‑client API shaping

## 06-case-studies

Work each as: requirements → estimates → API → data model → scale → failure modes → trade‑offs.

- [ ] Design an LLM chat product (streaming, history, rate limits, cost) — *start here, it's your domain*
- [ ] WhatsApp · [ ] Uber · [ ] YouTube · [ ] Dropbox
- [ ] URL shortener · [ ] Rate limiter · [ ] News feed

---

## Done when

Given a product, you can sketch an architecture on a whiteboard in 45 minutes: capacity estimates,
API, data model, where the caches/queues/replicas go, the top 3 failure modes, and a clear statement
of what each decision costs.

## Resources

- *Designing Data‑Intensive Applications* — the core text for this domain
- *System Design Interview* vol. 1 & 2 (Alex Xu) — for the case‑study format
- The "System Design Primer" repo · AWS Architecture Center write‑ups · company engineering blogs
