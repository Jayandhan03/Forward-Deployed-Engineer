"""Session & unit of work: how the ORM tracks changes and when SQL actually runs.

Session = a workspace + one transaction. It tracks objects you load/add (the IDENTITY MAP: one object per
row per session), collects changes, and on flush() emits the INSERT/UPDATE/DELETEs in the right order (UNIT
OF WORK). commit() = flush + COMMIT. In a web app: ONE session per request.

Needs: pip install sqlalchemy      Run:  python session-and-unit-of-work.py
"""

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str]
    balance: Mapped[int]


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(engine, expire_on_commit=False)    # factory; expire_on_commit=False keeps objects usable after commit

sql_log: list[str] = []
@event.listens_for(engine, "before_cursor_execute")
def log_sql(conn, cursor, statement, *args):
    sql_log.append(statement.split("\n")[0][:60])


def show(label):
    print(f"{label:34} SQL so far: {len(sql_log)}")


with SessionLocal() as s:
    a = Account(owner="ana", balance=100)
    s.add(a)
    show("1. after add() (nothing sent)")           # pending object: no INSERT yet
    s.flush()
    show("2. after flush()")                        # INSERT sent, still inside the transaction, not committed
    print("   a.id assigned by flush:", a.id)
    s.commit()
    show("3. after commit()")

    x = s.get(Account, a.id)                        # identity map: same row -> SAME Python object
    y = s.scalars(select(Account).where(Account.owner == "ana")).one()
    print("4. identity map: x is y ->", x is y)

    x.balance -= 30                                 # change tracking: just mutate attributes, no explicit update()
    print("5. session.dirty:", [repr(o.owner) for o in s.dirty])
    s.commit()                                      # UPDATE emitted automatically

# Rollback discards pending work, and the session is usable afterwards.
with SessionLocal() as s:
    acc = s.get(Account, 1)
    acc.balance = 0
    s.flush()                                       # change is in the DB transaction, not committed
    s.rollback()
    print("6. after rollback balance:", s.get(Account, 1).balance)

# The standard pattern: a context manager around one unit of work (this is what FastAPI's get_db dependency does).
try:
    with SessionLocal() as s, s.begin():            # begin() = commit on success, rollback on exception
        s.get(Account, 1).balance -= 10
        raise RuntimeError("boom, e.g. payment API failed")
except RuntimeError:
    pass
with SessionLocal() as s:
    print("7. after exception inside begin():", s.get(Account, 1).balance, "<- unchanged")

# expire_on_commit: default True marks objects stale after commit, so touching them RELOADS (extra query).
# That's correct for sync code, but breaks async code (no lazy IO), hence expire_on_commit=False there.
print("\nFastAPI pattern:\n  def get_db():\n      with SessionLocal() as db:\n          yield db        # one session per request, closed after\n")
print("Rules: don't share a session across threads/requests; commit once per use-case; flush() to get IDs early;")
print("rollback on error; never keep a session open during slow external calls.")
