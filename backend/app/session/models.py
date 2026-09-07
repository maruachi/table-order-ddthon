"""U4 Session domain entities (TableSession + history snapshot).

Owned by U4 (Session+Realtime). All models inherit the shared U0 ``Base`` and
carry ``store_id`` for tenant isolation (NFR-3). ``TableSession`` is the
usage unit for a table; ``SessionHistoryOrder`` / ``SessionHistoryOrderLine``
are self-contained snapshots captured at session close (Contract C, Q2/Q3=A)
so history reads (US-A7) never depend on U3 at runtime.

Importing this module registers the models on ``Base.metadata``.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base


class TableSession(Base):
    __tablename__ = "table_sessions"
    __table_args__ = (
        # BR-U4-1: at most one active session per table (SQLite partial unique).
        Index(
            "uq_active_session_per_table",
            "store_id",
            "table_id",
            unique=True,
            sqlite_where=text("status='active'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    table_id: Mapped[int] = mapped_column(
        ForeignKey("tables.id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active"
    )
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    history_orders: Mapped[list["SessionHistoryOrder"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionHistoryOrder(Base):
    __tablename__ = "session_history_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("table_sessions.id"), index=True, nullable=False
    )
    # Denormalized for read convenience (history filtering by table).
    table_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False)
    order_status: Mapped[str] = mapped_column(String(32), nullable=False)
    order_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    session: Mapped["TableSession"] = relationship(back_populates="history_orders")
    lines: Mapped[list["SessionHistoryOrderLine"]] = relationship(
        back_populates="history_order", cascade="all, delete-orphan"
    )


class SessionHistoryOrderLine(Base):
    __tablename__ = "session_history_order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    history_order_id: Mapped[int] = mapped_column(
        ForeignKey("session_history_orders.id"), index=True, nullable=False
    )
    menu_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)

    history_order: Mapped["SessionHistoryOrder"] = relationship(
        back_populates="lines"
    )
