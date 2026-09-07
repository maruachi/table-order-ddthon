"""Order domain models (U3) — Order, OrderItem.

Owned by U3. Tenant-scoped via ``store_id`` (NFR-3). ``session_id`` / ``menu_id``
are integer references to entities owned by other units (U4 / U2); no DB FK is
declared across unit boundaries (parallel dev / mocking). Menu name & unit price
are snapshotted onto OrderItem at write time so orders stay consistent even if a
menu later changes or is removed (BR-U3-3).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base

# Order status values (BR-U3-10). Free transitions among these (Q5).
ORDER_STATUS_PENDING = "pending"      # 대기중
ORDER_STATUS_PREPARING = "preparing"  # 준비중
ORDER_STATUS_DONE = "done"            # 완료
ORDER_STATUSES = (ORDER_STATUS_PENDING, ORDER_STATUS_PREPARING, ORDER_STATUS_DONE)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "order_no", name="uq_order_store_no"),
        Index("ix_order_store_session", "store_id", "session_id"),
        Index("ix_order_store_table", "store_id", "table_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    # Store-scoped human-facing sequential number (BR-U3-6).
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # Active session id obtained via Contract B (owned by U4; not a DB FK).
    session_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    table_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ORDER_STATUS_PENDING
    )
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Contract C: set when the session is closed (history handoff). Excluded
    # from current-session queries once true (BR-U3-7/14).
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Soft delete (BR-U3-9, US-A5).
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # store_id duplicated on the line so BaseRepository can scope it if needed.
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), index=True, nullable=False
    )
    # Reference to the menu (owned by U2); not a cross-unit DB FK.
    menu_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshots captured at order time (BR-U3-3).
    menu_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
