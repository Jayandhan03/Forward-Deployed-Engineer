-- PostgreSQL basics: types, CRUD, NULL semantics, psql survival kit.
--
-- Run Postgres:   docker run --name pg -e POSTGRES_PASSWORD=pw -p 5432:5432 -d postgres:16
-- Connect:        docker exec -it pg psql -U postgres        (or: psql postgresql://postgres:pw@localhost:5432/postgres)
-- Run this file:  psql postgresql://postgres:pw@localhost:5432/postgres -f postgres-basics.sql
--
-- psql meta-commands (not SQL, psql only):
--   \l  list databases    \c name  connect      \dt  list tables      \d table  describe a table
--   \di list indexes      \x       expanded output (great for wide rows)   \timing  show query time   \q  quit

DROP TABLE IF EXISTS notes;

-- ---- Types you will actually use -------------------------------------------------------------
CREATE TABLE notes (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- auto-increment (preferred over serial)
    public_id   uuid          NOT NULL DEFAULT gen_random_uuid(),   -- safe to expose in URLs (built in since PG13)
    title       text          NOT NULL,                             -- text: no length limit, no perf penalty vs varchar
    priority    integer       NOT NULL DEFAULT 3,
    price       numeric(10,2),                                      -- exact decimals: ALWAYS for money (never float)
    done        boolean       NOT NULL DEFAULT false,
    meta        jsonb         NOT NULL DEFAULT '{}',                -- semi-structured data, indexable (GIN)
    tags        text[]        NOT NULL DEFAULT '{}',                -- arrays are first class
    created_at  timestamptz   NOT NULL DEFAULT now()                -- timestamptz stores UTC; plain "timestamp" does not
);

-- ---- CREATE -----------------------------------------------------------------------------------
INSERT INTO notes (title, priority, price, meta, tags) VALUES
    ('write report',  1, 19.99, '{"owner": "ana", "client": {"name": "Acme"}}', ARRAY['work','urgent']),
    ('buy milk',      3, NULL,  '{"owner": "bo"}',                              ARRAY['home']),
    ('call dentist',  2, 0.10,  '{}',                                           '{}')
RETURNING id, public_id, title;                                      -- RETURNING gives back generated values: no 2nd query

-- ---- READ -------------------------------------------------------------------------------------
SELECT id, title, priority FROM notes WHERE priority <= 2 ORDER BY priority, id LIMIT 10;
SELECT title FROM notes WHERE title ILIKE '%MILK%';                  -- ILIKE = case-insensitive LIKE (Postgres only)

-- jsonb: -> returns json, ->> returns text, @> means "contains"
SELECT title, meta->>'owner' AS owner, meta->'client'->>'name' AS client FROM notes;
SELECT title FROM notes WHERE meta @> '{"owner": "ana"}';
SELECT title FROM notes WHERE 'urgent' = ANY(tags);                  -- array membership

-- ---- UPDATE / DELETE: ALWAYS check the WHERE clause first (run it as a SELECT) ---------------
UPDATE notes SET done = true, priority = priority + 1 WHERE title = 'buy milk' RETURNING id, done, priority;
DELETE FROM notes WHERE title = 'call dentist' RETURNING id;

-- Upsert: insert, or update if the unique key already exists (needs a UNIQUE/PK constraint on the target)
ALTER TABLE notes ADD CONSTRAINT notes_title_key UNIQUE (title);
INSERT INTO notes (title, priority) VALUES ('buy milk', 9)
    ON CONFLICT (title) DO UPDATE SET priority = EXCLUDED.priority
    RETURNING id, title, priority;

-- ---- NULL semantics: NULL means "unknown", not zero or empty ----------------------------------
SELECT NULL = NULL AS eq,                 -- NULL (not true!): comparing with unknown is unknown
       NULL IS NULL AS is_null,           -- true: the only correct test
       NULL IS DISTINCT FROM NULL AS d,   -- false: null-safe comparison
       COALESCE(NULL, 'fallback') AS co;  -- first non-null value
SELECT title, price FROM notes WHERE price = NULL;      -- returns NOTHING (classic bug)
SELECT title, price FROM notes WHERE price IS NULL;     -- correct
SELECT count(*) AS all_rows, count(price) AS non_null_prices FROM notes;   -- count(col) skips NULLs
-- NOT IN with a NULL in the list returns no rows ever: prefer NOT EXISTS.

-- ---- Time: store timestamptz, convert at the edges --------------------------------------------
SELECT now() AS utc_now, now() AT TIME ZONE 'Asia/Kolkata' AS local_time, now() - interval '7 days' AS week_ago;

-- ---- Inspect ----------------------------------------------------------------------------------
-- \d notes
SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'notes' ORDER BY ordinal_position;

-- Cleanup:  DROP TABLE notes;
