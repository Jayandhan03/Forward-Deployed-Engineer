"""Indexes you can SEE: the same query before and after an index, on SQLite (stdlib only, runs anywhere).

SQLite's `EXPLAIN QUERY PLAN` plays the role of Postgres's `EXPLAIN`: SCAN = read every row,
SEARCH ... USING INDEX = jump to matching rows. Timings and the write-cost tradeoff are real too.

Run:  python index_demo.py
"""

import random
import sqlite3
import time

random.seed(1)
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, user_id INT, kind TEXT, created INT)")
rows = [(random.randint(1, 10_000), random.choice(["click", "view", "buy"]), i) for i in range(300_000)]


def timed(fn):
    t = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - t) * 1000


def plan(sql):
    return " | ".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN " + sql))


_, insert_plain = timed(lambda: con.executemany("INSERT INTO events (user_id, kind, created) VALUES (?,?,?)", rows))
Q = "SELECT * FROM events WHERE user_id = 42"

print("1. no index  :", plan(Q))
_, ms = timed(lambda: [con.execute(Q).fetchall() for _ in range(50)])
print(f"   50 lookups: {ms:7.1f} ms")

con.execute("CREATE INDEX idx_user ON events (user_id)")
print("\n2. with index:", plan(Q))
_, ms2 = timed(lambda: [con.execute(Q).fetchall() for _ in range(50)])
print(f"   50 lookups: {ms2:7.1f} ms  (~{ms / max(ms2, 0.01):.0f}x faster)")

# Composite index: column order matters (leftmost prefix)
con.execute("CREATE INDEX idx_user_created ON events (user_id, created)")
print("\n3. composite (user_id, created):")
print("   filter user_id + sort created :", plan("SELECT * FROM events WHERE user_id = 42 ORDER BY created"))
print("   filter on created ONLY        :", plan("SELECT * FROM events WHERE created = 5"))   # leading column missing -> scan

# Function on the column defeats the index; an expression index fixes it
print("\n4. function on column:", plan("SELECT * FROM events WHERE upper(kind) = 'BUY'"))
con.execute("CREATE INDEX idx_kind_upper ON events (upper(kind))")
print("   after expression index:", plan("SELECT * FROM events WHERE upper(kind) = 'BUY'"))

# Writes get slower: every index must be updated on INSERT
con.execute("DROP TABLE events")
con.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, user_id INT, kind TEXT, created INT)")
for name, ddl in [("a", "CREATE INDEX a1 ON events(user_id)"), ("b", "CREATE INDEX b1 ON events(kind)"),
                  ("c", "CREATE INDEX c1 ON events(created)")]:
    con.execute(ddl)
_, insert_indexed = timed(lambda: con.executemany("INSERT INTO events (user_id, kind, created) VALUES (?,?,?)", rows))
print(f"\n5. bulk insert 300k rows: no index {insert_plain:6.0f} ms  vs  3 indexes {insert_indexed:6.0f} ms  <- the write cost")

print("\nTakeaway: index what you filter/join/sort on, check the plan, and don't index everything.")
