-- Constraints & views (PostgreSQL 13+).
-- Run: psql postgresql://postgres:pw@localhost:5432/postgres -f constraints-and-views.sql
--
-- Constraints make invalid data IMPOSSIBLE, no matter which service, script or person writes to the DB.
-- Application validation can be bypassed (a bug, a migration, a second service); constraints can't.

DROP MATERIALIZED VIEW IF EXISTS daily_revenue;
DROP VIEW IF EXISTS active_subscriptions;
DROP TABLE IF EXISTS bookings, subscriptions, plans, accounts CASCADE;

CREATE TABLE accounts (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,                 -- PK = UNIQUE + NOT NULL
    email      text    NOT NULL,
    age        integer CHECK (age BETWEEN 13 AND 120),                          -- CHECK: any boolean rule on the row
    status     text    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    CONSTRAINT accounts_email_format CHECK (email LIKE '%_@_%.__%')             -- NAME constraints: errors become readable
);
CREATE UNIQUE INDEX accounts_email_uq ON accounts (lower(email));               -- UNIQUE via a (case-insensitive) index

CREATE TABLE plans (
    id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      text    NOT NULL UNIQUE,
    price_cents integer NOT NULL CHECK (price_cents >= 0)
);

-- FOREIGN KEY actions decide what happens to children when the parent row is deleted:
--   ON DELETE RESTRICT/NO ACTION  refuse the delete (default; safest for important data)
--   ON DELETE CASCADE             delete children too (owned data: an account's sessions)
--   ON DELETE SET NULL            keep child, clear the link (optional relationship)
CREATE TABLE subscriptions (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  bigint NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    plan_id     bigint NOT NULL REFERENCES plans(id)    ON DELETE RESTRICT,     -- can't delete a plan people pay for
    started_at  timestamptz NOT NULL DEFAULT now(),
    ended_at    timestamptz,
    CHECK (ended_at IS NULL OR ended_at > started_at)                           -- cross-column rule
);

-- PARTIAL UNIQUE INDEX: "at most ONE active subscription per account" (active = ended_at IS NULL)
CREATE UNIQUE INDEX one_active_sub_per_account ON subscriptions (account_id) WHERE ended_at IS NULL;

-- EXCLUSION constraint: no overlapping bookings for the same room (needs btree_gist for the = operator)
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE bookings (
    id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room    integer   NOT NULL,
    during  tstzrange NOT NULL,
    EXCLUDE USING gist (room WITH =, during WITH &&)                            -- same room AND overlapping time = rejected
);

-- ---- Seed, then prove constraints reject bad data (each "FAILS" line should error; run them one by one) ----
INSERT INTO accounts (email, age) VALUES ('ana@x.com', 30), ('bo@x.com', NULL);   -- NULL passes CHECK (unknown is not false)
INSERT INTO plans (name, price_cents) VALUES ('free', 0), ('pro', 2900);
INSERT INTO subscriptions (account_id, plan_id) VALUES (1, 2);
INSERT INTO bookings (room, during) VALUES (1, tstzrange('2026-11-20 09:00+00', '2026-11-20 10:00+00'));

-- FAILS: INSERT INTO accounts (email, age) VALUES ('ANA@x.com', 20);                         -- duplicate (case-insens.)
-- FAILS: INSERT INTO accounts (email, age) VALUES ('nope', 20);                              -- accounts_email_format
-- FAILS: INSERT INTO accounts (email, age) VALUES ('kid@x.com', 5);                          -- age CHECK
-- FAILS: INSERT INTO subscriptions (account_id, plan_id) VALUES (1, 1);                      -- 2nd active sub
-- FAILS: DELETE FROM plans WHERE id = 2;                                                     -- RESTRICT
-- FAILS: INSERT INTO bookings (room, during) VALUES (1, tstzrange('2026-11-20 09:30+00', '2026-11-20 11:00+00'));  -- overlap

-- Adding a constraint to a big live table: NOT VALID first (instant, checks only new rows), then VALIDATE later
-- (scans without blocking writes). Avoids a long lock in production.
ALTER TABLE accounts ADD CONSTRAINT accounts_status_nonempty CHECK (length(status) > 0) NOT VALID;
ALTER TABLE accounts VALIDATE CONSTRAINT accounts_status_nonempty;

-- ---- VIEWS: a saved query that looks like a table. No data stored; always current. ----
CREATE VIEW active_subscriptions AS
SELECT s.id, a.email, p.name AS plan, p.price_cents, s.started_at
FROM subscriptions s
JOIN accounts a ON a.id = s.account_id
JOIN plans p    ON p.id = s.plan_id
WHERE s.ended_at IS NULL AND a.status = 'active';
SELECT * FROM active_subscriptions;
-- Use views to: hide complexity, give reporting users a stable shape, and expose only safe columns (no password_hash).
-- Views do NOT make queries faster by themselves.

-- MATERIALIZED VIEW: stores the result (fast reads, stale until refreshed). Good for expensive dashboards.
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT date_trunc('day', s.started_at) AS day, sum(p.price_cents) AS revenue_cents
FROM subscriptions s JOIN plans p ON p.id = s.plan_id
GROUP BY 1;
CREATE UNIQUE INDEX daily_revenue_day ON daily_revenue (day);                   -- required for CONCURRENTLY
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;                           -- refresh without blocking readers
SELECT * FROM daily_revenue;

-- Rule: put invariants in the DB (NOT NULL, FK, UNIQUE, CHECK), put business workflow in the app.
