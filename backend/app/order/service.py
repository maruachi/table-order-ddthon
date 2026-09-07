"""Order service (U3) — business logic & orchestration.

Implements BR-U3-1..14: order creation (Contract A menu validation -> Contract B
session -> persist -> Contract D publish), current-session listing, detail,
status change, soft delete + total recompute, dashboard snapshot, and the
Contract C history-handoff methods consumed by U4.
"""
from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common import events, realtime
from app.common.exceptions import NotFoundError, ValidationError
from app.common.security import StoreContext
from app.order.gateways import MenuLookup, SessionGateway
from app.order.models import ORDER_STATUS_PENDING, ORDER_STATUSES, Order, OrderItem
from app.order.repository import OrderRepository

logger = logging.getLogger(__name__)

_MAX_ORDER_NO_RETRIES = 3


class OrderService:
    def __init__(
        self,
        db: Session,
        menu_lookup: MenuLookup,
        session_gateway: SessionGateway,
    ):
        self.db = db
        self.repo = OrderRepository(db)
        self.menu = menu_lookup
        self.sessions = session_gateway

    # --- create (US-C4) ---------------------------------------------------
    def create_order(self, ctx: StoreContext, data_items: list) -> Order:
        """data_items: list of objects/dicts with .menu_id and .qty."""
        if ctx.table_id is None:
            raise ValidationError("table context required to create an order")

        items = [(_get(i, "menu_id"), _get(i, "qty")) for i in data_items]
        if not items:
            raise ValidationError("order requires at least one item")  # BR-U3-1
        for _mid, qty in items:
            if qty is None or qty <= 0:
                raise ValidationError("item qty must be >= 1")  # BR-U3-2

        # Contract A: validate menus & get authoritative prices (BR-U3-3).
        menu_ids = [mid for mid, _q in items]
        catalog = {m.id: m for m in self.menu.get_menu_items(ctx.store_id, menu_ids)}
        for mid in menu_ids:
            info = catalog.get(mid)
            if info is None or not info.available:
                raise ValidationError(f"menu {mid} is unavailable")

        # Contract B: obtain/start active session (BR-U3-4). Failure aborts.
        try:
            session_id = self.sessions.start_or_get_active_session(
                ctx.store_id, ctx.table_id
            )
        except Exception as exc:  # noqa: BLE001 - surface as domain error
            logger.exception("session gateway failed store=%s", ctx.store_id)
            raise ValidationError("could not start table session") from exc

        # Build order + items with price snapshots (BR-U3-3/5).
        order = self._persist_order(ctx, session_id, items, catalog)

        # Contract D: publish after commit-worthy state (best-effort, BR-U3-11).
        realtime.publish(
            ctx.store_id,
            events.order_created(
                ctx.store_id,
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "session_id": order.session_id,
                    "table_id": order.table_id,
                    "status": order.status,
                    "total": order.total,
                },
            ),
        )
        return order

    def _persist_order(self, ctx, session_id, items, catalog) -> Order:
        last_exc: Exception | None = None
        for _attempt in range(_MAX_ORDER_NO_RETRIES):
            order_no = self.repo.next_order_no(ctx.store_id)
            order = Order(
                store_id=ctx.store_id,
                order_no=order_no,
                session_id=session_id,
                table_id=ctx.table_id,
                status=ORDER_STATUS_PENDING,
                total=0,
            )
            total = 0
            for mid, qty in items:
                info = catalog[mid]
                line_total = info.price * qty
                total += line_total
                order.items.append(
                    OrderItem(
                        store_id=ctx.store_id,
                        menu_id=mid,
                        menu_name=info.name,
                        unit_price=info.price,
                        qty=qty,
                        line_total=line_total,
                    )
                )
            order.total = total
            self.db.add(order)
            try:
                self.db.flush()
                return order
            except IntegrityError as exc:  # order_no race (BR-U3-6)
                self.db.rollback()
                last_exc = exc
                logger.warning("order_no collision store=%s, retrying", ctx.store_id)
        raise ValidationError("could not assign order number") from last_exc

    # --- read (US-C5 / US-A3) --------------------------------------------
    def list_current_session_orders(
        self, ctx: StoreContext, offset: int = 0, limit: int = 50
    ) -> tuple[list[Order], int]:
        if ctx.table_id is None:
            raise ValidationError("table context required")
        session_id = self.sessions.get_active_session(ctx.store_id, ctx.table_id)
        if session_id is None:
            return [], 0  # BR-U3-7: no active session -> empty
        orders = list(
            self.repo.list_active_by_session(
                ctx.store_id, session_id, offset=offset, limit=limit
            )
        )
        total = self.repo.count_active_by_session(ctx.store_id, session_id)
        return orders, total

    def get_order(self, ctx: StoreContext, order_id: int) -> Order:
        order = self.repo.get_with_items(ctx.store_id, order_id)
        if order is None or order.is_deleted:  # BR-U3-9
            raise NotFoundError("order not found")
        # BR-U3-8: a table may only read its own active session's orders.
        if ctx.role == "table":
            active = self.sessions.get_active_session(ctx.store_id, ctx.table_id)
            if order.session_id != active:
                raise NotFoundError("order not found")
        return order

    # --- status change (US-A3) -------------------------------------------
    def update_order_status(
        self, ctx: StoreContext, order_id: int, status: str
    ) -> Order:
        if status not in ORDER_STATUSES:  # BR-U3-10
            raise ValidationError("invalid status")
        order = self.repo.get(ctx.store_id, order_id)
        if order is None or order.is_deleted:
            raise NotFoundError("order not found")
        order.status = status  # free transition (Q5)
        self.db.flush()
        realtime.publish(
            ctx.store_id,
            events.order_status_changed(
                ctx.store_id,
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "session_id": order.session_id,
                    "table_id": order.table_id,
                    "status": order.status,
                },
            ),
        )
        return order

    # --- delete (US-A5) ---------------------------------------------------
    def delete_order(self, ctx: StoreContext, order_id: int):
        order = self.repo.get(ctx.store_id, order_id)
        if order is None or order.is_deleted:
            raise NotFoundError("order not found")
        self.repo.soft_delete(order)  # BR-U3-9
        table_total = self.repo.sum_active_total_for_table(
            ctx.store_id, order.table_id
        )  # BR-U3-12
        realtime.publish(
            ctx.store_id,
            events.order_deleted(
                ctx.store_id,
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "table_id": order.table_id,
                    "session_id": order.session_id,
                    "table_total": table_total,
                },
            ),
        )
        return {"table_id": order.table_id, "total": table_total}

    # --- dashboard snapshot (US-A2 initial, Q4) ---------------------------
    def get_dashboard_snapshot(
        self, ctx: StoreContext, table_filter: int | None = None, latest_n: int = 3
    ) -> list[dict]:
        orders = list(self.repo.list_active_by_store(ctx.store_id))
        cards: dict[int, dict] = {}
        for order in orders:
            if table_filter is not None and order.table_id != table_filter:
                continue
            card = cards.setdefault(
                order.table_id,
                {"table_id": order.table_id, "total": 0, "order_count": 0, "latest_orders": []},
            )
            card["total"] += order.total
            card["order_count"] += 1
            if len(card["latest_orders"]) < latest_n:
                card["latest_orders"].append(order)  # already desc by created_at
        return list(cards.values())

    # --- Contract C: history handoff (called by U4 close_session) ---------
    def collect_active_session_orders(
        self, store_id: int, session_id: int
    ) -> list[Order]:
        return list(self.repo.list_active_session_orders(store_id, session_id))

    def mark_orders_archived(self, store_id: int, order_ids: list[int]) -> int:
        return self.repo.mark_archived(store_id, order_ids)  # idempotent (BR-U3-14)


def _get(item, attr):
    if isinstance(item, dict):
        return item.get(attr)
    return getattr(item, attr, None)
