# Proof of Work

The portfolio. Recruiters, founders, and collaborators should scroll your GitHub + X and think:
*"This person ships, learns, and explains."* This folder tracks the production‑grade builds and the
write‑ups that prove it.

## The bar for a "production‑quality" build

Not a tutorial. Each of the 3–5 flagship products should have **all** of:

- [ ] Authentication (+ OAuth) and user management
- [ ] Payments / billing (Stripe) where it makes sense
- [ ] Real AI workflows (streaming, tools, RAG, or agents — not a single GPT call)
- [ ] Production deployment (HTTPS, domain, CI/CD)
- [ ] Monitoring — logs, metrics, error tracking, an uptime check
- [ ] Analytics — basic product funnel
- [ ] Background jobs / workers
- [ ] A real database with migrations
- [ ] A polished, responsive UI
- [ ] Documentation — README, architecture doc, API docs

## Candidate flagship products

Pick 3–5. See [`product-ideas.md`](product-ideas.md) for the full list. Strong picks for an AI
product engineer:

- AI research assistant · AI meeting assistant · AI customer support · AI CRM
- AI browser/automation agent · AI finance dashboard · AI content system

## Structure

- [`writeups/`](writeups/) — one technical write‑up per project: the hard parts, the trade‑offs, the numbers.
- [`benchmarks/`](benchmarks/) — sync vs async, retrieval quality, cost per request, latency profiles. Charts, not adjectives.

## What principal‑level proof looks like

Beyond the code: documented **architecture decisions**, clear **trade‑off analysis**, **cost awareness**
($/request, $/user), **reliability** work (SLOs, incident notes), and **write‑ups** other engineers cite.
