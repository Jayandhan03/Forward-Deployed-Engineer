"""Transactions you can run: atomic rollback, the lost-update bug, and the atomic-SQL fix. (SQLite, stdlib.)

SQLite has a single writer, so it can't show Postgres's isolation levels. It CAN show the two things you hit
daily: (1) a failed transaction leaves no half-done state, (2) read-modify-write in app code loses updates
while `UPDATE ... SET x = x - n` does not. Two threads stand in for two concurrent web requests.

Run:  python transaction_demo.py
"""

import os
import sqlite3
import tempfile
import threading
import time

db_path = os.path.join(tempfile.mkdtemp(), "demo.db")


def connect():
    con = sqlite3.connect(db_path, timeout=10, isolation_level=None)   # autocommit; we issue BEGIN/COMMIT ourselves
    return con


def reset():
    con = connect()
    con.executescript("""DROP TABLE IF EXISTS accounts;
        CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER NOT NULL CHECK (balance >= 0));
        INSERT INTO accounts VALUES (1, 100), (2, 50);""")
    con.close()


def balances():
    con = connect()
    rows = con.execute("SELECT id, balance FROM accounts ORDER BY id").fetchall()
    con.close()
    return rows


# 1. Atomicity ------------------------------------------------------------------------------------------------
reset()
con = connect()
try:
    con.execute("BEGIN")
    con.execute("UPDATE accounts SET balance = balance + 500 WHERE id = 2")      # step 1 succeeds...
    con.execute("UPDATE accounts SET balance = balance - 500 WHERE id = 1")      # step 2 violates CHECK (100 - 500 < 0)
    con.execute("COMMIT")
except sqlite3.IntegrityError as e:
    con.execute("ROLLBACK")
    print("1. step 2 failed:", e, "-> rolled back")
con.close()
print("   balances (unchanged, step 1 undone too):", balances())

# 2. Lost update ------------------------------------------------------------------------------------------------
def withdraw_unsafe(amount):
    con = connect()
    (bal,) = con.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()   # read
    time.sleep(0.05)                                                                # app logic / network call in between
    con.execute("UPDATE accounts SET balance = ? WHERE id = 1", (bal - amount,))    # write a value computed from a STALE read
    con.close()


def withdraw_atomic(amount):
    con = connect()
    con.execute("UPDATE accounts SET balance = balance - ? WHERE id = 1", (amount,))   # DB does read+modify+write atomically
    con.close()


def run_concurrently(fn):
    reset()
    threads = [threading.Thread(target=fn, args=(10,)) for _ in range(5)]            # 5 simultaneous requests, 10 each
    [t.start() for t in threads]
    [t.join() for t in threads]
    return balances()[0][1]


print("\n2. five concurrent withdrawals of 10 from a balance of 100 (correct result: 50)")
print("   read-modify-write in app code :", run_concurrently(withdraw_unsafe), " <- lost updates")
print("   UPDATE SET balance = balance-n:", run_concurrently(withdraw_atomic), " <- correct")

print("\nTakeaways: group dependent writes in one transaction; never compute new values from stale reads;")
print("push the arithmetic into SQL, or lock with SELECT ... FOR UPDATE, or use a version column + retry.")
