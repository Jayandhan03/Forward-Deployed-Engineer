-- Indexes (PostgreSQL 13+). Run with:  psql ... -f indexes.sql
-- Pair with index_demo.py (runnable anywhere, shows the effect on SQLite).
--
-- An index is a separate sorted structure (B-tree by default) that lets the DB jump to rows instead of
-- reading the whole table (a "sequential scan"). It makes READS faster and WRITES slower (every INSERT /
-- UPDATE / DELETE must also update each index) and costs disk. Index what you filter, join and sort on.

DROP TABLE IF EXISTS events;
CREATE TABLE events (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,    -- PK gets a unique index automatically
    user_id     integer     NOT NULL,
    kind        text        NOT NULL,
    status      text        NOT NULL,
    payload     jsonb       NOT NULL DEFAULT '{}',
    created_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO events (user_id, kind, status, payload, created_at)
SELECT (random() * 10000)::int,
       (ARRAY['click', 'view', 'buy'])[1 + (random() * 2)::int],
       CASE WHEN random() < 0.01 THEN 'failed' ELSE 'ok' END,                       -- 1% failed = a skewed column
       jsonb_build_object('plan', (ARRAY['free', 'pro'])[1 + (random())::int]),
       now() - (random() * interval '90 days')
FROM generate_series(1, 500000);
ANALYZE events;                                                                      -- refresh planner statistics

-- 1. Baseline: no index on user_id -> Seq Scan over 500k rows
EXPLAIN ANALYZE SELECT * FROM events WHERE user_id = 42;

-- 2. B-tree index -> Index/Bitmap Scan. Foreign keys, WHERE, JOIN and ORDER BY columns are candidates.
CREATE INDEX events_user_id_idx ON events (user_id);
EXPLAIN ANALYZE SELECT * FROM events WHERE user_id = 42;

-- 3. COMPOSITE index: column ORDER matters (leftmost-prefix rule). Put equality columns first, range/sort last.
CREATE INDEX events_user_created_idx ON events (user_id, created_at DESC);
EXPLAIN ANALYZE SELECT * FROM events WHERE user_id = 42 ORDER BY created_at DESC LIMIT 20;   -- uses both columns, no sort
EXPLAIN SELECT * FROM events WHERE created_at > now() - interval '1 day';                   -- can't use it well: leading col missing

-- 4. PARTIAL index: index only the rows you query. 1% failed rows -> tiny, fast index.
CREATE INDEX events_failed_idx ON events (created_at) WHERE status = 'failed';
EXPLAIN ANALYZE SELECT * FROM events WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;

-- 5. COVERING index (INCLUDE): store extra columns in the index so the query never touches the table (Index Only Scan).
CREATE INDEX events_user_cover_idx ON events (user_id) INCLUDE (kind);
VACUUM events;                                                                       -- index-only scans need a fresh visibility map
EXPLAIN ANALYZE SELECT user_id, kind FROM events WHERE user_id = 42;

-- 6. EXPRESSION index: the query must use the SAME expression
CREATE INDEX events_lower_kind_idx ON events (lower(kind));
EXPLAIN SELECT * FROM events WHERE lower(kind) = 'buy';

-- 7. GIN index for jsonb containment (@>) and full-text / array search
CREATE INDEX events_payload_gin ON events USING gin (payload);
EXPLAIN SELECT * FROM events WHERE payload @> '{"plan": "pro"}';

-- 8. When the planner IGNORES an index (on purpose or by your mistake):
--    * low selectivity: kind has 3 values, so a scan of 1/3 of the table is cheaper than jumping around -> Seq Scan
EXPLAIN SELECT * FROM events WHERE kind = 'view';
--    * function on the column:  WHERE date(created_at) = '2026-11-01'  -> rewrite as a range:
--      WHERE created_at >= '2026-11-01' AND created_at < '2026-11-02'
--    * type mismatch / implicit cast, a leading wildcard  LIKE '%abc',  or stale statistics (run ANALYZE).
--    * tiny tables: a seq scan is just faster.

-- 9. Build on a live production table WITHOUT blocking writes (cannot run inside a transaction):
CREATE INDEX CONCURRENTLY events_status_idx ON events (status);

-- 10. Housekeeping: find unused indexes (they cost writes for nothing) and the sizes
SELECT relname AS table, indexrelname AS index, idx_scan AS times_used, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes WHERE relname = 'events' ORDER BY idx_scan;

-- Rules: index foreign keys + frequent filters/sorts; verify with EXPLAIN ANALYZE; fewer, well-chosen indexes beat many;
-- every index slows writes; drop the unused ones.
