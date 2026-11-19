-- EXPLAIN ANALYZE & query tuning (PostgreSQL 13+).
-- Run after indexes.sql so the `events` table exists (500k rows), or:  psql ... -f ../../05-indexes/practice/indexes.sql
--
-- EXPLAIN          shows the plan the planner WOULD use (estimates only, query is not run)
-- EXPLAIN ANALYZE  actually RUNS it and shows real times + row counts  (careful with UPDATE/DELETE: wrap in BEGIN ... ROLLBACK)
-- Add BUFFERS to see how much data was read from cache vs disk:  EXPLAIN (ANALYZE, BUFFERS) ...

-- ---- How to read a plan (read from the innermost / most indented node outward) ---------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id, count(*) AS n FROM events WHERE created_at > now() - interval '7 days' GROUP BY user_id ORDER BY n DESC LIMIT 5;
--  Limit  (cost=0.00..1.2 rows=5 ...) (actual time=41.3..41.3 rows=5 loops=1)
--    -> Sort ...
--       -> HashAggregate ...
--          -> Seq Scan on events  (cost=0..11000 rows=38000) (actual time=0.02..30 rows=39000 loops=1)
--               Filter: (created_at > ...)    Rows Removed by Filter: 461000
-- Things to look at:
--   cost=a..b        planner's made-up units: startup..total. Compare plans with it, don't read it as milliseconds.
--   rows=  vs  actual rows=   BIG MISMATCH (10x+) = bad statistics -> run ANALYZE, or the planner picks a bad plan.
--   actual time=a..b ms to first row..all rows, PER LOOP. Multiply by loops for the node's total.
--   Rows Removed by Filter   huge number = you're reading far more than you return -> missing/unusable index.
--   Buffers: shared hit / read   hit = from memory, read = from disk.
--   Execution Time   the number you actually care about.

-- ---- Scan types ------------------------------------------------------------------------------------
--  Seq Scan           reads the whole table. Fine for small tables or when returning a big share of rows.
--  Index Scan         walks the index, fetches each row from the table. Few rows.
--  Index Only Scan    answered from the index alone (covering index). Fastest.
--  Bitmap Index Scan  + Bitmap Heap Scan: collect matching row locations, then read table pages in order. Medium selectivity.

-- ---- Join algorithms --------------------------------------------------------------------------------
--  Nested Loop   for each outer row, look up inner (great when outer is small AND inner has an index; bad on big x big)
--  Hash Join     build a hash table of the smaller side, probe with the other (equality joins, no index needed)
--  Merge Join    both sides sorted, walk together (large pre-sorted inputs)

-- ---- Statistics: the planner guesses from them. Stale stats = bad plans. ---------------------------------
ANALYZE events;                                                              -- refresh (autovacuum does this regularly)
SELECT attname, n_distinct, null_frac FROM pg_stats WHERE tablename = 'events' AND attname IN ('user_id', 'status');

-- ---- Tuning loop: measure -> find the slowest node -> change ONE thing -> measure again ---------------
-- Fix 1: missing index
EXPLAIN ANALYZE SELECT * FROM events WHERE user_id = 7 AND kind = 'buy';
CREATE INDEX IF NOT EXISTS events_user_kind_idx ON events (user_id, kind);
EXPLAIN ANALYZE SELECT * FROM events WHERE user_id = 7 AND kind = 'buy';

-- Fix 2: function on an indexed column prevents the index. Rewrite as a range.
EXPLAIN SELECT * FROM events WHERE date_trunc('day', created_at) = '2026-11-01';                                    -- Seq Scan
EXPLAIN SELECT * FROM events WHERE created_at >= '2026-11-01' AND created_at < '2026-11-02';                        -- index-friendly

-- Fix 3: SELECT only what you need (SELECT * blocks index-only scans and moves more data)
EXPLAIN ANALYZE SELECT user_id, kind FROM events WHERE user_id = 7;

-- Fix 4: OFFSET pagination reads and throws away rows. Use keyset pagination.
EXPLAIN ANALYZE SELECT * FROM events ORDER BY id OFFSET 400000 LIMIT 10;                                            -- slow: skips 400k
EXPLAIN ANALYZE SELECT * FROM events WHERE id > 400000 ORDER BY id LIMIT 10;                                        -- fast: index seek

-- Fix 5: N+1 (an ORM runs 1 + N queries). See 04-orm-sqlalchemy/05-n-plus-one-problem: use a JOIN or selectin loading.
-- Fix 6: count(*) on huge tables is a full scan. Use an estimate (pg_class.reltuples) or a maintained counter if exact isn't needed.
SELECT reltuples::bigint AS estimated_rows FROM pg_class WHERE relname = 'events';

-- ---- Safe EXPLAIN ANALYZE on a write: roll it back ----------------------------------------------------
BEGIN;
EXPLAIN ANALYZE UPDATE events SET status = 'ok' WHERE status = 'failed';
ROLLBACK;

-- ---- Find slow queries in production: pg_stat_statements ---------------------------------------------
-- Needs `shared_preload_libraries = 'pg_stat_statements'` in postgresql.conf, then:  CREATE EXTENSION pg_stat_statements;
-- SELECT calls, round(mean_exec_time::numeric, 2) AS mean_ms, round(total_exec_time::numeric) AS total_ms, left(query, 80) AS query
-- FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
--   total_exec_time (not just slowest single query) finds the real cost: a 5 ms query called 10M times beats one 2 s report.
-- Also: log_min_duration_statement = 500   logs every query slower than 500 ms.
