# 02 · AI Engineering

The layer on top of standard backend work once an LLM is part of the product. This is where your
existing ML/DL/NLP/GenAI foundation converts into **production** capability — moving from *calling* an
API to *engineering* a system around a non‑deterministic, metered, fallible dependency.

**Depth target:** L4–5. **Budget:** 5–6 weeks. Builds directly on domain 01 (streaming, workers, storage, DB).

---

## 00-llm-apis

Treat the model as a metered external resource, not a free function.

- [ ] Provider clients — OpenAI, Anthropic, Google Gemini; one thin internal abstraction over them
- [ ] Chat & messages API — roles, multi‑turn, message shaping
- [ ] Streaming tokens — server‑side handling, backpressure, partial parsing
- [ ] Context windows — budgeting input vs output, truncation strategy
- [ ] Sampling parameters — temperature, top‑p, penalties; when determinism matters
- [ ] Token accounting & cost — count before send, log per‑request cost, budget alarms
- [ ] Retries, fallbacks & timeouts — provider outage → degrade, not crash
- [ ] Prompt & response caching — exact‑match and semantic; provider prompt caching

## 01-prompting

- [ ] Prompt structure — instruction / context / examples / output contract
- [ ] Few‑shot examples — selection, ordering, when they hurt
- [ ] System / developer / user roles — what belongs where
- [ ] **Structured outputs** — JSON schema / response format; validation & repair loop
- [ ] **Tool calling** — schema design, parallel calls, result feedback, error handling
- [ ] Reasoning models — when the extra latency/cost is worth it
- [ ] Prompt versioning & testing — prompts are code; diff them, test them

## 02-embeddings-and-vector-search

- [ ] Embeddings basics — what the vector means, model choice, dimensionality
- [ ] Similarity metrics — cosine vs dot vs L2, normalization
- [ ] pgvector — vectors alongside your relational data (default choice)
- [ ] Qdrant — a dedicated vector DB; when you outgrow pgvector
- [ ] ANN indexes — HNSW, IVF; recall vs latency vs memory
- [ ] Hybrid search — BM25/keyword + vector, fusion (RRF)

## 03-rag

- [ ] Ingestion pipeline — load → clean → chunk → embed → upsert; incremental
- [ ] Chunking strategies — fixed / recursive / semantic / structural; overlap
- [ ] Retrieval — top‑k, filters, metadata, multi‑query
- [ ] Reranking — cross‑encoder / LLM rerank; when it earns its cost
- [ ] Context assembly — ordering, dedup, budget, citations inline
- [ ] Citations & grounding — force the model to cite; detect ungrounded claims
- [ ] RAG evaluation — retrieval hit‑rate, answer faithfulness, end‑to‑end
- [ ] Incremental & scheduled reindexing — freshness without full rebuilds

## 04-evaluation

Outputs are non‑deterministic — you need a deliberate way to catch quality regressions.

- [ ] Building eval datasets — golden sets, from real traffic, edge cases
- [ ] LLM‑as‑judge — rubric design, bias, pairwise vs pointwise
- [ ] Prompt regression testing — run the suite on every prompt change (in CI)
- [ ] Latency & cost metrics — p50/p95, tokens, $/request as first‑class metrics
- [ ] Hallucination detection — grounding checks, self‑consistency, NLI
- [ ] Offline vs online eval — CI gate vs production sampling & feedback

## 05-multimodal

- [ ] Vision / image input · [ ] OCR pipeline · [ ] Speech‑to‑text · [ ] Text‑to‑speech
- [ ] Audio pipeline (chunking, diarization, streaming) · [ ] Image generation

## 06-fine-tuning

- [ ] **When NOT to fine‑tune** — prompt / RAG / tools first, almost always
- [ ] Data preparation — format, dedup, split, leakage
- [ ] LoRA basics — what it changes, memory footprint
- [ ] Evaluating a tuned model — against the base, on held‑out and live data

---

## Projects for this domain

`projects/07` AI chat backend (streaming, history, tool calls) → `projects/08` RAG API
(ingestion, hybrid retrieval, citations, eval harness).

## Done when

You can design a RAG service with an eval suite in CI, a per‑request cost log, provider fallback, and a
reindex job — and explain each retrieval/chunking/rerank choice with a number, not a vibe.

## Resources

- Provider docs: Anthropic, OpenAI, Google — read the tool‑use and structured‑output guides in full.
- `references/` in the local **claude-api** skill for Anthropic model IDs, pricing, caching, token counting.
- Anthropic "Building effective agents"; OpenAI evals cookbook; pgvector + Qdrant docs.
- Papers: RAG (Lewis 2020), HNSW (Malkov 2018), RRF — skim for intuition.
