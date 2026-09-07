"""Order repository (U3) — store-scoped persistence (NFR-3).

Extends U0 ``BaseRepository`` (which enforces ``store_id`` on every query) with
order-specific reads: sequential numbering, active-session listing, store-wide
active listing, and total aggregation. "Active" = not archived and not deleted
(BR-U3-7).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.common.repository import BaseRepository
from app.order.models import Order


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(db, Order)

    # --- numbering (BR-U3-6) ---------------------------------------------
    def next_order_no(self, store_id: int) -> int:
        """Next store-scoped sequential order number (max + 1)."""
        current_max = self.db.scalar(
            select(func.max(Order.order_no)).where(Order.store_id == store_id)
        )
        return int(current_max or 0) + 1

    # --- reads ------------------------------------------------------------
    def get_with_items(self, store_id: int, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.store_id == store_id, Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return self.db.scalars(stmt).first()

    def list_active_by_session(
        self, store_id: int, session_id: int, *, offset: int = 0, limit: int = 50
    ) -> Sequence[Order]:
        stmt = (
            self._active_scope(store_id)
            .where(Order.session_id == session_id)
            .order_by(Order.created_at.asc(), Order.id.asc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Order.items))
        )
        return self.db.scalars(stmt).all()

    def count_active_by_session(self, store_id: int, session_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(
                Order.store_id == store_id,
                Order.session_id == session_id,
                Order.archived.is_(False),
                Order.is_deleted.is_(False),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def list_active_by_store(self, store_id: int) -> Sequence[Order]:
        stmt = (
            self._active_scope(store_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .options(selectinload(Order.items))
        )
        return self.db.scalars(stmt).all()

    def list_active_session_orders(
        self, store_id: int, session_id: int
    ) -> Sequence[Order]:
        """All active orders for a session (Contract C collect), with items."""
        stmt = (
            self._active_scope(store_id)
            .where(Order.session_id == session_id)
            .order_by(Order.created_at.asc(), Order.id.asc())
            .options(selectinload(Order.items))
        )
        return self.db.scalars(stmt).all()

    def sum_active_total_for_table(self, store_id: int, table_id: int) -> int:
        stmt = select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.store_id == store_id,
            Order.table_id == table_id,
            Order.archived.is_(False),
            Order.is_deleted.is_(False),
        )
        return int(self.db.scalar(stmt) or 0)

    # --- writes -----------------------------------------------------------
    def soft_delete(self, order: Order) -> None:
        order.is_deleted = True
        order.deleted_at = datetime.now(timezone.utc)
        self.db.flush()

    def mark_archived(self, store_id: int, order_ids: list[int]) -> int:
        """Contract C: flag orders as archived (idempotent, BR-U3-14)."""
        if not order_ids:
            return 0
        orders = self.db.scalars(
            self._scoped(store_id).where(Order.id.in_(order_ids))
        ).all()
        changed = 0
        for order in orders:
            if not order.archived:
                order.archived = True
                changed += 1
        self.db.flush()
        return changed

    # --- helpers ----------------------------------------------------------
    def _active_scope(self, store_id: int):
        return self._scoped(store_id).where(
            Order.archived.is_(False), Order.is_deleted.is_(False)
        )
