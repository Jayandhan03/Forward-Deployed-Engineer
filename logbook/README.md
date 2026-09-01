# Logbook

The daily record. This is how "I studied for 6 months" becomes a visible, searchable track record.

## The loop (every study session)

1. **Learn** one concept (one topic file in a domain folder).
2. **Implement** it — in a `projects/` build or a runnable snippet next to the topic file.
3. **Write** the topic file (notes, questions you can now answer cold, "done when", links).
4. **Commit** — `<area>: <what changed>`.
5. **Log** — copy [`_templates/til.md`](_templates/til.md) into `YYYY/YYYY-MM-DD.md`, fill it in.
6. **Post** — turn the TIL into an X post (draft from [`_templates/x-post.md`](_templates/x-post.md)) with code / a diagram / a benchmark.
7. **Check the box** in [`../PROGRESS.md`](../PROGRESS.md).

## Files

```
logbook/
  2026/
    2026-09-01.md        # one file per study day
    ...
  _templates/
    til.md               # daily "today I learned"
    x-post.md            # X post draft
    weekly-review.md     # every Sunday
```

## Weekly (Sunday)

Copy [`_templates/weekly-review.md`](_templates/weekly-review.md) into `YYYY/YYYY-Www.md`. Review what
moved, what stalled, and set next week's focus. Tag a git checkpoint if a project shipped.

## Posting cadence

- **Daily:** one small artifact — "TIL why dependency injection in FastAPI improves testability" + code.
- **Weekly:** a slightly bigger piece — a benchmark, a diagram, a mini write‑up.
- **Per project:** a thread or short walkthrough video, linked from the project README.

Keep posts practical: show code, diagrams, or numbers. Over months this compounds into the portfolio.
