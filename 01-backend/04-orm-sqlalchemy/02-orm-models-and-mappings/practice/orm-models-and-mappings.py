"""ORM models & mappings (SQLAlchemy 2.x style): Python classes <-> tables, fully typed.

`Mapped[type]` declares the Python type (and nullability: `Mapped[str | None]` = nullable column),
`mapped_column(...)` adds column details. Constraints and indexes belong in the model too, so the schema
is defined in ONE place (Alembic then generates the migration from it).

Needs: pip install sqlalchemy      Run:  python orm-models-and-mappings.py
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.schema import CreateTable


class Base(DeclarativeBase):                                  # one Base per app; holds the MetaData
    pass


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("org_id", "sku", name="uq_products_org_sku"),      # sku unique per org
        CheckConstraint("price >= 0", name="ck_products_price_nonneg"),
        Index("ix_products_org_name", "org_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)                        # int + primary_key -> autoincrement PK
    org_id: Mapped[int]                                                      # no mapped_column needed for plain NOT NULL int
    sku: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None]                                          # `| None` -> NULLABLE
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))                   # money = Numeric, never float
    active: Mapped[bool] = mapped_column(default=True)                       # Python-side default (applied by the ORM)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())  # DB-side default (works for raw SQL inserts too)

    def __repr__(self) -> str:
        return f"Product(id={self.id}, sku={self.sku!r}, price={self.price})"


if __name__ == "__main__":
    engine = create_engine("sqlite://")
    print(CreateTable(Product.__table__))                                    # the DDL SQLAlchemy derives from the class
    Base.metadata.create_all(engine)

    with Session(engine) as s:
        p = Product(org_id=1, sku="PEN-1", name="Pen", price=Decimal("1.50"))
        s.add(p)
        s.commit()                                                           # INSERT happens here
        print("after commit:", p, "| active default:", p.active, "| description:", p.description)

        s.add(Product(org_id=1, sku="PEN-1", name="Dup", price=Decimal("2")))     # violates uq_products_org_sku
        try:
            s.commit()
        except Exception as e:
            s.rollback()
            print("unique violated ->", type(e).__name__)

        s.add(Product(org_id=1, sku="NEG", name="Bad", price=Decimal("-1")))      # violates the CHECK
        try:
            s.commit()
        except Exception as e:
            s.rollback()
            print("check violated  ->", type(e).__name__)

        print("query:", s.scalars(select(Product).where(Product.org_id == 1)).all())

    print("\nRules: Mapped[] types drive nullability; keep constraints/indexes in the model; Numeric for money;")
    print("server_default for defaults that must also hold for non-ORM writers; `class Base(DeclarativeBase)` once per app.")
