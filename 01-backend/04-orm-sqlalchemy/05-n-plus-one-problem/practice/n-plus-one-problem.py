"""The N+1 query problem: 1 query for the list + N more, one per row, because related data loads lazily.

100 authors -> 101 queries instead of 1 or 2. Invisible in dev with 5 rows, painful in prod with 5000.
Find it: log SQL or COUNT queries in a test. Fix it: eager-load. Prevent it: raiseload + a query-count test.

Needs: pip install sqlalchemy      Run:  python n-plus-one-problem.py
"""

from contextlib import contextmanager

from sqlalchemy import ForeignKey, create_engine, event, select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, raiseload, relationship, selectinload


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[Author] = relationship(back_populates="books")


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
statements: list[str] = []


@event.listens_for(engine, "before_cursor_execute")
def record(conn, cursor, statement, *args):
    statements.append(statement)


@contextmanager
def count_queries():
    statements.clear()
    yield statements                                           # the same list: inspect len() afterwards


with Session(engine) as s:
    s.add_all([Author(name=f"a{i}", books=[Book(title=f"b{i}-{j}") for j in range(3)]) for i in range(100)])
    s.commit()


def titles_by_author(authors):
    return {a.name: [b.title for b in a.books] for a in authors}


# 1. THE BUG: the loop touches `a.books`, each access fires its own SELECT
with Session(engine) as s, count_queries() as q:
    titles_by_author(s.scalars(select(Author)))
    print(f"1. lazy loading : {len(q)} queries   <- 1 + N (N = 100 authors)")
    print("   repeated SQL :", q[1].split("WHERE")[0].strip().replace("\n", " ")[:70], "... WHERE author_id = ?  (x100)")

# 2. FIX: eager load with selectinload -> 2 queries total, regardless of N
with Session(engine) as s, count_queries() as q:
    titles_by_author(s.scalars(select(Author).options(selectinload(Author.books))))
    print(f"2. selectinload : {len(q)} queries")

# 3. PREVENT: raiseload turns a forgotten eager-load into a loud error instead of a silent slowdown
with Session(engine) as s:
    authors = s.scalars(select(Author).options(raiseload(Author.books))).all()
    try:
        authors[0].books
    except InvalidRequestError as e:
        print("3. raiseload    : lazy access blocked ->", str(e).split(" - ")[0][:60])

# 4. TEST IT: a query-count assertion keeps the fix from regressing (put this in your test suite)
def test_author_listing_is_not_n_plus_one():
    with Session(engine) as s, count_queries() as q:
        titles_by_author(s.scalars(select(Author).options(selectinload(Author.books))))
        assert len(q) <= 2, f"N+1 detected: {len(q)} queries"


test_author_listing_is_not_n_plus_one()
print("4. query-count test passed")

print("\nSpot it: SQLAlchemy echo=True / a slow endpoint with many near-identical SELECTs in the log / APM trace.")
print("Fix it: selectinload for collections, joinedload for many-to-one, or write one JOIN query yourself.")
print("Prevent it: lazy='raise' (or raiseload) on relationships in API code + query-count assertions in tests.")
