-- Transactions & isolation levels (PostgreSQL 13+).
-- Most examples need TWO psql sessions open side by side: call them  [A]  and  [B].
-- Setup (either session):  psql postgresql://postgres:pw@localhost:5432/postgres -f transactions-and-isolation.sql
--
-- ACID:  Atomic (all or nothing) | Consistent (constraints hold) | Isolated (concurrent txns don't see each other's
--        half-done work) | Durable (committed = survives a crash).
-- MVCC:  Postgres keeps multiple row versions, so READERS NEVER BLOCK WRITERS and vice versa. Only writers on the
--        SAME row block each other.

DROP TABLE IF EXISTS accounts, tickets;
CREATE TABLE accounts (id int PRIMARY KEY, owner text, balance int NOT NULL CHECK (balance >= 0));
INSERT INTO accounts VALUES (1, 'ana', 100), (2, 'bo', 50);
CREATE TABLE tickets (id int PRIMARY KEY, left_ int NOT NULL);
INSERT INTO tickets VALUES (1, 1);

-- ---- 1. Atomicity: a transfer is two updates that must succeed or fail together --------------------------
BEGIN;
UPDATE accounts SET balance = balance - 30 WHERE id = 1;
UPDATE accounts SET balance = balance + 30 WHERE id = 2;
COMMIT;                                      -- or ROLLBACK; to undo both. A crash before COMMIT = neither applied.
-- In an app: one transaction per request/use-case, open late, commit early, no network calls (LLM/HTTP) inside it.

-- ---- 2. Lost update (the classic bug) -------------------------------------------------------------------
-- Two requests each read balance=70, compute 70-10 in app code, write 60. One withdrawal vanishes.
--   [A] BEGIN; SELECT balance FROM accounts WHERE id=1;          -- 70
--   [B] BEGIN; SELECT balance FROM accounts WHERE id=1;          -- 70
--   [A] UPDATE accounts SET balance = 60 WHERE id=1; COMMIT;
--   [B] UPDATE accounts SET balance = 60 WHERE id=1; COMMIT;     -- should be 50. Lost update.
-- Fix A (best): do the math in SQL, atomically:   UPDATE accounts SET balance = balance - 10 WHERE id = 1;
-- Fix B: lock the row while you decide:
--   [A] BEGIN; SELECT balance FROM accounts WHERE id=1 FOR UPDATE;   -- locks the row
--   [B] BEGIN; SELECT balance FROM accounts WHERE id=1 FOR UPDATE;   -- WAITS here until A commits, then reads the new value
-- Fix C: optimistic locking: add a `version` column:  UPDATE ... SET ..., version = version + 1 WHERE id=1 AND version = :seen
--        and retry if 0 rows were updated.
-- Queue pattern: workers grab jobs without colliding:
--   SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;

-- ---- 3. Isolation levels ---------------------------------------------------------------------------------
--  READ COMMITTED (default)  each STATEMENT sees data committed before it started. Non-repeatable reads possible.
--  REPEATABLE READ           the whole transaction sees one snapshot from its first query. Stable reports. Can fail with
--                            "could not serialize access" -> RETRY the transaction.
--  SERIALIZABLE              behaves as if transactions ran one at a time. Prevents write skew. Retry on serialization failure.
-- (Postgres has no real READ UNCOMMITTED: dirty reads never happen.)
--
-- Non-repeatable read at READ COMMITTED:
--   [A] BEGIN; SELECT balance FROM accounts WHERE id=2;          -- 80
--   [B] UPDATE accounts SET balance = 0 WHERE id=2;              -- autocommits
--   [A] SELECT balance FROM accounts WHERE id=2;                 -- 0  (changed mid-transaction)
-- Same steps with  BEGIN ISOLATION LEVEL REPEATABLE READ;  in [A] -> second SELECT still shows 80.

-- ---- 4. Write skew (needs SERIALIZABLE or an explicit lock) ---------------------------------------------
-- Rule: at least one doctor on call. Two doctors both check "2 on call, safe to leave" and both leave -> zero on call.
-- Each txn read rows the other wrote, but they updated DIFFERENT rows, so row locks never collide.
-- REPEATABLE READ allows it; SERIALIZABLE aborts one of them. Or lock the set: SELECT ... FOR UPDATE on the rows you rely on.

-- ---- 5. Deadlocks ----------------------------------------------------------------------------------------
--   [A] BEGIN; UPDATE accounts SET balance = balance WHERE id = 1;
--   [B] BEGIN; UPDATE accounts SET balance = balance WHERE id = 2;
--   [A] UPDATE accounts SET balance = balance WHERE id = 2;      -- waits for B
--   [B] UPDATE accounts SET balance = balance WHERE id = 1;      -- waits for A -> Postgres detects it, aborts one: "deadlock detected"
-- Prevention: always lock rows in the SAME ORDER (e.g. ORDER BY id), keep transactions short, retry on deadlock error.

-- ---- 6. Advisory locks: app-level mutex via the DB (e.g. "only one instance runs this cron job") ---------
SELECT pg_try_advisory_lock(42) AS got_it;      -- true for the first session, false for others; release with pg_advisory_unlock(42)
-- Inside a txn, pg_advisory_xact_lock(42) auto-releases at COMMIT/ROLLBACK (safer).

-- ---- 7. Prove atomicity on one session --------------------------------------------------------------------
BEGIN;
UPDATE accounts SET balance = balance - 1000 WHERE id = 1;     -- violates CHECK (balance >= 0) -> error
ROLLBACK;                                                      -- after an error the txn is aborted; ROLLBACK is required
SELECT * FROM accounts ORDER BY id;                            -- unchanged: ana 70, bo 80
