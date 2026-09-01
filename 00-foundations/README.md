# 00 · Foundations

Everything above this layer assumes a rough model of what's happening underneath. You don't need to
be a hardware engineer — just not mystified. **Get this to "I can reason about why my system behaves
this way," then move on** and let it deepen as real problems force it.

**Depth target:** L3 (can use it, can reason about it). Don't perfect it before touching backend.
**Budget:** 3–4 weeks. Concurrency and the Python‑deep section are the parts that pay off daily.

---

## 00-computer-bedrock

- [ ] **Binary & number systems** — why float rounding, integer overflow, and encoding bugs happen.
- [ ] **CPU, registers, RAM & cache** — why "memory access is slow" is the reason performance engineering exists.
- [ ] **OS fundamentals** — processes vs threads, scheduling, virtual memory. What running a program actually does.
- [ ] **File systems** — what "saving a file" does on disk, and why it can fail halfway through.
- [ ] **Networking basics** — TCP/IP, ports, packets. The plumbing every API call travels through.
- [ ] **How the internet works** — DNS, routing, client‑server, TLS handshake — URL typed → page rendered.
- [ ] **The command line** — navigating, piping, scripting without a GUI.

## 01-python-deep

Learn the transferable stuff once, deeply, in Python.

- [ ] **Data model & dunders** — `__init__`, `__repr__`, `__eq__`, `__iter__`, `__enter__`… how Python objects really work.
- [ ] **Mutability, references vs values** — why mutating a list inside a function surprises you.
- [ ] **Scope, closures & namespaces** — LEGB, late binding, `nonlocal`.
- [ ] **Iterators & generators** — lazy evaluation, `yield`, generator pipelines.
- [ ] **Decorators** — wrapping behaviour; `functools.wraps`; parametrized decorators.
- [ ] **Context managers** — `with`, `contextlib`, cleanup guarantees.
- [ ] **Comprehensions & itertools** — and when a plain loop is clearer.
- [ ] **Exceptions & tracebacks** — reading a stack trace properly; custom exception hierarchies.
- [ ] **Type hints** — `typing`, generics, `Protocol`, `mypy`/`pyright`.
- [ ] **Dataclasses & namedtuples** — when each fits; `frozen`, `slots`.
- [ ] **Memory model, refcounting & GC** — cyclic references, `__del__`, `weakref`.
- [ ] **CPython internals & the GIL** — what the GIL does and doesn't block.
- [ ] **Packaging, pip & virtual environments** — `pyproject.toml`, `uv`/`poetry`, lockfiles, editable installs.

## 02-data-structures

Vocabulary for describing how data is organized. Implement each once; know the trade‑offs.

- [ ] Arrays & dynamic arrays · [ ] Linked lists · [ ] Stacks & queues · [ ] Hash tables
- [ ] Trees & BST · [ ] Heaps & priority queues · [ ] Graphs · [ ] Tries
- [ ] Bloom filters · [ ] LRU cache · [ ] Union‑find

## 03-algorithms

Not competitive‑programming depth — enough to reason about why something is slow.

- [ ] Sorting · [ ] Searching (binary search & variants) · [ ] Recursion & backtracking
- [ ] Graph algorithms (BFS, DFS, Dijkstra, topological sort) · [ ] Dynamic programming basics
- [ ] **Big‑O & complexity analysis** — time and space, amortized, worst vs average.

## 04-concurrency

The layer most backend bugs live in.

- [ ] Processes vs threads · [ ] CPU‑bound vs I/O‑bound (which one asyncio helps)
- [ ] Threading & thread pools · [ ] Multiprocessing
- [ ] **Asyncio & the event loop** — coroutines, tasks, `await`, blocking‑call hazards
- [ ] Locks, semaphores, queues · [ ] Race conditions & deadlocks
- [ ] Profiling & benchmarking — `cProfile`, `py-spy`, `timeit`, `pytest-benchmark`

## 05-engineering-practice

Habits that separate "code that runs" from code a team maintains.

- [ ] **Git** — branching, merging, rebasing, resolving conflicts (used every day here)
- [ ] OOP thinking — when it helps · [ ] Functional thinking
- [ ] Design patterns — factory, strategy, observer… and when *not* to
- [ ] Clean code & SOLID — writing for the next person (usually you in six months)
- [ ] Testing — unit / integration / e2e; what's worth testing
- [ ] Code review — giving feedback that improves code, taking it without ego
- [ ] Debugging — a real debugger (`pdb`/`debugpy`), not print‑and‑hope

---

## Mini‑projects (pick 2–3)

- **CLI tool** — argument parsing, config file, logging, packaged and `pip install`‑able.
- **File processor** — walk a directory tree, transform files, handle partial failure and resume.
- **Mini in‑memory key‑value store** — with an LRU eviction policy and a TTL.
- **Concurrency benchmark** — same workload sync vs threads vs asyncio vs multiprocessing; chart it.

## Done when

You can: read a stack trace and a `cProfile` dump and say what's wrong; explain when asyncio helps and
when it doesn't; pick the right data structure for a lookup‑heavy vs ordered‑iteration workload and
justify it; rebase a feature branch and resolve a conflict without googling every step.

## Resources

- *Fluent Python* (Ramalho) — Python data model, chapters 1, 7–9, 17–21.
- *CPython Internals* (Shaw) — skim.
- MIT 6.006 lectures — data structures & algorithms.
- `pdb`/`debugpy` docs; *Computer Systems: A Programmer's Perspective* — chapters 1, 6, 9 (reference, not cover‑to‑cover).
