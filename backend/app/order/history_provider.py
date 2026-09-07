"""Contract C provider implementation (U3 -> U4 history handoff / dashboard).

U4 collects a session's live orders both for the admin dashboard preview
(US-A5) and to snapshot them into history at session close (US-A6/A7). U3
implements the ``OrderHistoryProvider`` protocol here and registers it at app
startup, mirroring the ``register_publisher`` pattern.

The protocol passes no DB session, so the provider opens its own short-lived
``SessionLocal``. Reads are lock-free. In ``close_session`` U4 defers all of its
writes to a single final commit (autoflush is off), so the archive commit here
lands cleanly on its own connection before U4 commits — no SQLite write-lock
contention. (The two writes are not one transaction; on the rare failure of
U4's final commit an order could be archived without a history row. Acceptable
for the local demo.)
"""
from __future__ import annotations

from typing import Any

from app.common.database import SessionLocal
from app.order.repository import OrderRepository


class OrderHistoryProviderImpl:
    """Real Contract C provider backed by the U3 order tables."""

    def collect_active_session_orders(
        self, store_id: int, session_id: int
    ) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            repo = OrderRepository(db)
            orders = repo.list_active_session_orders(store_id, session_id)
            return [
                {
                    # order_id is additive (Contract C history ignores it; the
                    # dashboard uses it to open an order for management).
                    "order_id": o.id,
                    "order_no": str(o.order_no),
                    "order_status": o.status,
                    "order_amount": o.total,
                    "ordered_at": o.created_at,
                    "lines": [
                        {
                            "menu_name": it.menu_name,
                            "quantity": it.qty,
                            "unit_price": it.unit_price,
                        }
                        for it in o.items
                    ],
                }
                for o in orders
            ]
        finally:
            db.close()

    def mark_orders_archived(self, store_id: int, session_id: int) -> None:
        db = SessionLocal()
        try:
            repo = OrderRepository(db)
            orders = repo.list_active_session_orders(store_id, session_id)
            repo.mark_archived(store_id, [o.id for o in orders])
            db.commit()
        finally:
            db.close()
