"""Relationships & loading strategies: one-to-many, many-to-many, cascades, lazy vs selectin vs joined.

`relationship()` lets you navigate objects (author.books) instead of writing joins. The FK column lives on
the "many" side; `back_populates` links both directions. HOW related rows get loaded decides how many
queries run: that is the N+1 topic's root cause.

Needs: pip install sqlalchemy      Run:  python relationships-and-loading.py
"""

from sqlalchemy import Column, ForeignKey, Table, create_engine, event, select
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, joinedload, mapped_column, relationship, selectinload)


class Base(DeclarativeBase):
    pass


# Many-to-many needs an association table (here without extra columns; with extras make it a full model).
book_tags = Table("book_tags", Base.metadata,
                  Column("book_id", ForeignKey("books.id"), primary_key=True),
                  Column("tag_id", ForeignKey("tags.id"), primary_key=True))


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # one-to-many. cascade: deleting an author deletes their books; removing a book from the list deletes it (orphan)
    books: Mapped[list["Book"]] = relationship(back_populates="author", cascade="all, delete-orphan")


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))          # FK on the MANY side
    author: Mapped[Author] = relationship(back_populates="books")
    tags: Mapped[list["Tag"]] = relationship(secondary=book_tags, back_populates="books")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    books: Mapped[list[Book]] = relationship(secondary=book_tags, back_populates="tags")


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
queries = 0
@event.listens_for(engine, "before_cursor_execute")
def count(*a):
    global queries
    queries += 1


def measure(label, fn):
    global queries
    queries = 0
    out = fn()
    print(f"{label:34} -> {queries} queries  {out}")


with Session(engine) as s:
    fiction, sci = Tag(name="fiction"), Tag(name="science")
    s.add_all([Author(name=f"author{i}", books=[Book(title=f"book{i}-{j}", tags=[fiction if j else sci]) for j in range(2)])
               for i in range(5)])
    s.commit()

with Session(engine) as s:
    # 1. Default LAZY loading: related rows are fetched on first access, one query per object.
    measure("lazy (default)", lambda: [len(a.books) for a in s.scalars(select(Author))])
with Session(engine) as s:
    # 2. selectinload: ONE extra query using IN (...). Best default for collections (one-to-many, many-to-many).
    measure("selectinload(Author.books)", lambda: [len(a.books) for a in s.scalars(select(Author).options(selectinload(Author.books)))])
with Session(engine) as s:
    # 3. joinedload: single query with a JOIN. Best for many-to-ONE (book.author); for collections it multiplies rows.
    measure("joinedload(Book.author)", lambda: len([b.author.name for b in s.scalars(select(Book).options(joinedload(Book.author))).unique()]))
with Session(engine) as s:
    # 4. Chain them: authors -> books -> tags
    measure("selectinload(books).selectinload(tags)", lambda: sum(len(b.tags) for a in s.scalars(
        select(Author).options(selectinload(Author.books).selectinload(Book.tags))) for b in a.books))

with Session(engine) as s:                                                # cascades in action
    a = s.scalars(select(Author).limit(1)).one()
    a.books.pop()                                                         # orphan -> deleted on flush
    s.flush()
    print("\nbooks after removing one from author0:", len(a.books), "| total in DB:", s.query(Book).count())
    s.delete(a)                                                           # cascade deletes remaining books
    s.flush()
    print("after deleting author0, total books:", s.query(Book).count())

print("\nPick: collection -> selectinload | many-to-one -> joinedload | rarely-used -> lazy.")
print("Cascade 'all, delete-orphan' only for OWNED children (order -> items), never for shared things (tags).")
