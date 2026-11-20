"""Alembic migrations: version-controlled schema changes (upgrade/downgrade), instead of editing the DB by hand.

Real workflow (CLI):
    alembic init migrations                    one time; then set sqlalchemy.url and target_metadata = Base.metadata in env.py
    alembic revision --autogenerate -m "add phone"   diff models vs DB -> writes migrations/versions/<id>_add_phone.py
    (REVIEW the file: autogenerate misses renames [sees drop+add], some constraints, server defaults, data)
    alembic upgrade head                       apply        |  alembic downgrade -1   undo the last one
    alembic current / alembic history          where am I / what exists
This script uses Alembic's Python API on SQLite to show the three core mechanics without needing a project folder:
(1) autogenerate's diff, (2) an upgrade operation, (3) a data migration, plus expand/contract notes.

Needs: pip install sqlalchemy alembic      Run:  python alembic-migrations.py
"""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect, text

engine = create_engine("sqlite://")

# --- v1 of the schema is already live in the database ---
v1 = MetaData()
Table("users", v1, Column("id", Integer, primary_key=True), Column("full_name", String, nullable=False))
v1.create_all(engine)
with engine.begin() as conn:
    conn.execute(text("INSERT INTO users (full_name) VALUES ('Ana Silva'), ('Bo Chen')"))

# --- your models now describe v2: a new `phone` column ---
metadata = MetaData()
Table("users", metadata, Column("id", Integer, primary_key=True), Column("full_name", String, nullable=False),
      Column("phone", String(20), nullable=True))

with engine.connect() as conn:
    # 1. what `alembic revision --autogenerate` does: compare models to the live DB
    diff = compare_metadata(MigrationContext.configure(conn), metadata)
    print("1. autogenerate sees:", [(d[0], d[2], d[3].name) for d in diff], "<- would become op.add_column(...)")

with engine.begin() as conn:
    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)

    # 2. upgrade(): the body of a generated migration file
    op.add_column("users", Column("phone", String(20), nullable=True))
    print("2. upgrade applied, columns now:", [c["name"] for c in inspect(conn).get_columns("users")])

    # 3. data migration: backfill in the SAME revision (or a separate one for big tables, in batches)
    conn.execute(text("ALTER TABLE users ADD COLUMN first_name TEXT"))
    conn.execute(text("UPDATE users SET first_name = substr(full_name, 1, instr(full_name, ' ') - 1)"))
    print("3. backfilled:", conn.execute(text("SELECT full_name, first_name FROM users")).all())

    # downgrade(): the inverse. batch_alter_table is how SQLite drops columns (Postgres: op.drop_column directly)
    with op.batch_alter_table("users") as batch:
        batch.drop_column("phone")
    print("   downgrade dropped phone:", [c["name"] for c in inspect(conn).get_columns("users")])

print("""
What a migration file looks like:
    revision = "a1b2c3"; down_revision = "9f8e7d"           <- a linked list of schema versions
    def upgrade():   op.add_column("users", sa.Column("phone", sa.String(20)))
    def downgrade(): op.drop_column("users", "phone")

Zero-downtime = EXPAND / CONTRACT (old and new app versions both run during a deploy):
    deploy 1 EXPAND   : add the new column as NULLABLE (never NOT NULL without a default on a big table: it locks it)
    deploy 2          : app writes both old+new; backfill old rows in batches
    deploy 3          : app reads only new
    deploy 4 CONTRACT : drop the old column
  A rename = add new + copy + switch + drop old. Never rename in one step.
Postgres tips: CREATE INDEX CONCURRENTLY needs op.get_context().autocommit_block(); set lock_timeout so a migration
fails fast instead of queueing behind a long query and blocking everyone.
CI/deploy: run `alembic upgrade head` as a release step BEFORE new app pods start; test it on a copy of prod-shaped data;
CI check: `alembic check` fails if models and migrations have drifted.""")
