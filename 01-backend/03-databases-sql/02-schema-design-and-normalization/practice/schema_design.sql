-- Schema design & normalization: model a small multi-tenant SaaS (orgs, users, projects, tags).
--
-- Run:  psql postgresql://postgres:pw@localhost:5432/postgres -f schema_design.sql   (PostgreSQL 13+)
--
-- Process: list the NOUNS (entities) -> decide how they relate (1:1, 1:N, N:M) -> give each a key
-- -> put every fact in exactly ONE place (normalization) -> add constraints so bad data can't exist.

DROP TABLE IF EXISTS project_tags, tags, tasks, projects, memberships, users, orgs CASCADE;

-- ---- Keys: surrogate (bigint identity or uuid) for the PK, natural keys (email, slug) as UNIQUE ----
CREATE TABLE orgs (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug        text        NOT NULL UNIQUE,                 -- natural key people use; never changes the PK
    name        text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       text        NOT NULL,
    full_name   text        NOT NULL,
    deleted_at  timestamptz,                                 -- soft delete: NULL = active, keeps history/FKs intact
    created_at  timestamptz NOT NULL DEFAULT now()
);
-- Unique email only among ACTIVE users, case-insensitive (partial + expression index in one)
CREATE UNIQUE INDEX users_email_active_uq ON users (lower(email)) WHERE deleted_at IS NULL;

-- ---- Many-to-many: users <-> orgs via a junction table (the extra columns live on the relationship) ----
CREATE TABLE memberships (
    org_id   bigint NOT NULL REFERENCES orgs(id)  ON DELETE CASCADE,
    user_id  bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role     text   NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    PRIMARY KEY (org_id, user_id)                            -- composite PK also prevents duplicates
);

-- ---- One-to-many: an org has many projects. The FK lives on the "many" side. ----
-- Multi-tenancy: every tenant-owned table carries org_id, and every query filters by it.
CREATE TABLE projects (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    org_id      bigint      NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name        text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (org_id, name)                                    -- name unique PER org, not globally
);
CREATE INDEX projects_org_id_idx ON projects (org_id);       -- Postgres does NOT auto-index foreign keys

CREATE TABLE tasks (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id  bigint  NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assignee_id bigint  REFERENCES users(id) ON DELETE SET NULL,     -- optional: NULL = unassigned
    title       text    NOT NULL,
    status      text    NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done'))
);
CREATE INDEX tasks_project_id_idx ON tasks (project_id);

-- ---- Many-to-many again: projects <-> tags ----
CREATE TABLE tags (
    id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  text NOT NULL UNIQUE
);
CREATE TABLE project_tags (
    project_id bigint NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tag_id     bigint NOT NULL REFERENCES tags(id)     ON DELETE CASCADE,
    PRIMARY KEY (project_id, tag_id)
);

-- ---- Normalization by example --------------------------------------------------------------------
-- BAD (one wide table):  tasks(title, project_name, org_name, assignee_name, assignee_email, tags_csv)
--   1NF violated: tags_csv packs many values in one column      -> use project_tags rows
--   2NF/3NF violated: org_name repeats on every task; rename an org and you must update N rows (or get conflicts)
--   -> each fact lives once: org name in orgs, user email in users; tasks only hold the foreign keys.
-- WHEN TO DENORMALIZE (on purpose, after measuring): read-heavy reports (store a cached task_count on projects),
--   immutable snapshots (invoice keeps the customer's address AT THE TIME), or jsonb for truly free-form attributes.
-- Rule of thumb: normalize first, denormalize only to fix a measured read problem, and keep the source of truth.

-- ---- Seed + prove the constraints work -------------------------------------------------------------
INSERT INTO orgs (slug, name) VALUES ('acme', 'Acme Inc'), ('globex', 'Globex');
INSERT INTO users (email, full_name) VALUES ('ana@acme.com', 'Ana'), ('bo@globex.com', 'Bo');
INSERT INTO memberships VALUES (1, 1, 'owner'), (2, 2, 'owner'), (1, 2, 'member');
INSERT INTO projects (org_id, name) VALUES (1, 'Website'), (1, 'Mobile'), (2, 'Website');   -- same name OK in another org
INSERT INTO tasks (project_id, assignee_id, title) VALUES (1, 1, 'Design homepage'), (1, NULL, 'Write copy');

-- Each of these must FAIL (uncomment one at a time):
-- INSERT INTO users (email, full_name) VALUES ('ANA@acme.com', 'Dup');                    -- case-insensitive unique
-- INSERT INTO projects (org_id, name) VALUES (1, 'Website');                              -- unique per org
-- INSERT INTO tasks (project_id, title, status) VALUES (1, 'x', 'banana');                -- CHECK
-- INSERT INTO tasks (project_id, title) VALUES (999, 'orphan');                           -- FK
-- DELETE FROM orgs WHERE id = 1;     -- succeeds and CASCADEs to projects/tasks/memberships: know your ON DELETE rules!
