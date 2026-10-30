"""Run storage schema: sessions -> runs -> steps, in SQLite so it runs anywhere.

The same tables port straight to Postgres. Answers: what happened in run X, what did it cost,
which runs failed today?

Run:
    python run_storage.py
"""

import json
import sqlite3
import time

SCHEMA = """
CREATE TABLE sessions (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    status TEXT NOT NULL CHECK (status IN ('queued','running','paused','done','failed')),
    task TEXT NOT NULL,
    started_at REAL, finished_at REAL, error TEXT
);
CREATE TABLE steps (
    run_id TEXT NOT NULL REFERENCES runs(id),
    idx INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('model','tool')),
    name TEXT NOT NULL,
    input TEXT, output TEXT,
    input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0,
    ms REAL,
    PRIMARY KEY (run_id, idx)
);
CREATE INDEX runs_by_status ON runs(status, started_at);
"""


def add_step(db, run_id, idx, kind, name, inp, out, tin=0, tout=0, ms=0.0):
    db.execute("INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?)",
               (run_id, idx, kind, name, json.dumps(inp), json.dumps(out), tin, tout, ms))


if __name__ == "__main__":
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    now = time.time()

    db.execute("INSERT INTO sessions VALUES ('s1','alice',?)", (now,))
    db.execute("INSERT INTO runs VALUES ('r1','s1','done','refund 881',?,?,NULL)", (now, now + 4))
    db.execute("INSERT INTO runs VALUES ('r2','s1','failed','refund 999',?,?,?)",
               (now, now + 2, "payments API timeout"))

    add_step(db, "r1", 0, "model", "claude-sonnet-5-5", {"msgs": 1}, {"tool": "lookup_order"}, 900, 60, 800)
    add_step(db, "r1", 1, "tool", "lookup_order", {"id": 881}, {"amount": 42}, 0, 0, 120)
    add_step(db, "r1", 2, "model", "claude-sonnet-5-5", {"msgs": 3}, {"text": "done"}, 1100, 40, 700)
    add_step(db, "r2", 0, "model", "claude-sonnet-5-5", {"msgs": 1}, {"tool": "refund_order"}, 900, 50, 750)

    print("failed runs:")
    for row in db.execute("SELECT id, task, error FROM runs WHERE status='failed'"):
        print("  ", row)

    print("\ntokens and time per run:")
    q = """SELECT run_id, COUNT(*) steps, SUM(input_tokens) tin, SUM(output_tokens) tout, ROUND(SUM(ms)) ms
           FROM steps GROUP BY run_id"""
    for row in db.execute(q):
        print("  ", row)

    print("\nreplay r1:")
    for idx, kind, name, out in db.execute("SELECT idx, kind, name, output FROM steps WHERE run_id='r1' ORDER BY idx"):
        print(f"   {idx} {kind:<5} {name:<18} -> {out}")
