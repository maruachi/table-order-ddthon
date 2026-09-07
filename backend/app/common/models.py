"""Common domain entities owned by U0 (Store, Table).

All tenant-scoped models across units carry a ``store_id`` FK for isolation
(NFR-3, BR-U0-1). ``Store`` itself is the tenant root.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Business identifier entered at login by admin / table tablet.
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    tables: Mapped[list["Table"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint("store_id", "table_number", name="uq_table_store_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    table_number: Mapped[str] = mapped_column(String(32), nullable=False)
    # bcrypt hash of the table password (hashing performed by U1 Auth).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    store: Mapped["Store"] = relationship(back_populates="tables")
