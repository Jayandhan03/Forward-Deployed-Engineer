"""SQLAlchemy Core: the engine, connections and the SQL expression language (no ORM classes).

Core = "SQL, but as Python objects": safe parameter binding, composable queries, works with any database.
The ORM (next topics) is built on top of this. Use Core for bulk work, reports and when you want to
see exactly what SQL runs. SQLite in memory here; for Postgres only the URL changes:
    postgresql+psycopg://user:pw@localhost:5432/db

Needs: pip install sqlalchemy      Run:  python sqlalchemy-core.py
"""

from sqlalchemy import (Column, ForeignKey, Integer, MetaData, String, Table, create_engine, func, insert, select,
                        text)

# Engine = connection pool + dialect. Create ONCE per process. echo=True prints every SQL statement.
engine = create_engine("sqlite+pysqlite:///:memory:", echo=False)

metadata = MetaData()
users = Table("users", metadata,
              Column("id", Integer, primary_key=True),
              Column("name", String(50), nullable=False),
              Column("country", String(2), nullable=False))
orders = Table("orders", metadata,
               Column("id", Integer, primary_key=True),
               Column("user_id", ForeignKey("users.id"), nullable=False),
               Column("total", Integer, nullable=False))
metadata.create_all(engine)                                   # CREATE TABLE IF NOT EXISTS (use Alembic in real projects)

# `begin()` = transaction: commits on success, rolls back on exception.
with engine.begin() as conn:
    conn.execute(insert(users), [{"name": "Ana", "country": "PT"}, {"name": "Bo", "country": "US"},
                                 {"name": "Cy", "country": "US"}])                # list of dicts = executemany (fast bulk insert)
    conn.execute(insert(orders), [{"user_id": 1, "total": 100}, {"user_id": 1, "total": 250}, {"user_id": 2, "total": 80}])

with engine.connect() as conn:                                # read-only use
    # Expression language: composable, parameters are ALWAYS bound (no SQL injection)
    q = (select(users.c.name, func.sum(orders.c.total).label("spent"))
         .join(orders, orders.c.user_id == users.c.id)
         .group_by(users.c.name)
         .having(func.sum(orders.c.total) > 90)
         .order_by(func.sum(orders.c.total).desc()))
    print("compiled SQL:\n", str(q), "\n")
    for row in conn.execute(q):
        print("row:", row.name, row.spent, "|", row._mapping)    # rows behave like named tuples

    # Raw SQL is fine too, but ALWAYS with :named parameters, never f-strings
    country = "US"
    print("text():", conn.execute(text("SELECT name FROM users WHERE country = :c ORDER BY id"), {"c": country}).scalars().all())

    evil = "x' OR '1'='1"
    safe = conn.execute(select(users.c.name).where(users.c.name == evil)).all()
    print("injection attempt returns:", safe, "<- bound as a plain value")

    print("scalar_one:", conn.execute(select(func.count()).select_from(users)).scalar_one())

# Pooling: connect() borrows from the pool, closing the `with` RETURNS it (doesn't disconnect). Tune with
# create_engine(..., pool_size=5, max_overflow=10, pool_pre_ping=True) for Postgres: pool_pre_ping drops dead connections.
print("\npool:", engine.pool.__class__.__name__)
print("Rules: one engine per app, short-lived connections via `with`, bind parameters, never string-format SQL.")
