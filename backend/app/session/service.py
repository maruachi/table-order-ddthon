"""U4 Session service — Contracts B (session lifecycle), C (order history),
D (realtime publish).

Owns the active-session guard (BR-U4-1/2), close-time snapshotting inside a
single transaction (BR-U4-4), the admin dashboard (US-A5) and history reads
(US-A7). ``store_id`` always originates from the authenticated context
(BR-U4-3); it is never taken from client input here.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.common.events import session_closed
from app.common.exceptions import NotFoundError
from app.common.models import Table
from app.common.realtime import publish
from app.common.repository import BaseRepository
from app.common.schemas import Page
from app.session.models import (
    SessionHistoryOrder,
    SessionHistoryOrderLine,
    TableSession,
)
from app.session.provider import get_order_provider
from app.session.repository import SessionRepository
from app.session.schemas import (
    ClosedSessionSummary,
    DashboardCard,
    HistoryOrderLineOut,
    HistoryOrderOut,
    RecentOrder,
)

_DEFAULT_PREVIEW_N = 3
# Upper bound above which preview_n is treated as invalid and reset (BR-U4-16).
_MAX_PREVIEW_N = 10
# Active sessions per store are bounded by table count; a generous cap here.
_ACTIVE_SCAN_LIMIT = 1000


def _now() -> datetime:
    # Naive UTC to match how SQLite persists/reads DateTime columns (it strips
    # tzinfo). This keeps ``closed_at`` the same shape on both /sessions/close
    # and /sessions/history. NOTE: history date filtering is therefore UTC-based
    # (BR-U4-8); day-boundary filtering by a non-UTC store calendar is out of
    # scope for the local demo.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SessionService:
    def __init__(self, db) -> None:
        self.db = db
        self.repo = SessionRepository(db)

    # --- Contract B: session lifecycle ------------------------------------
    def start_or_get_active_session(self, store_id: int, table_id: int) -> int:
        existing = self.repo.get_active(store_id, table_id)
        if existing is not None:
            return existing.id  # idempotent (BR-U4-2)
        try:
            session = self.repo.create_active(store_id, table_id)
            self.db.flush()
            return session.id
        except IntegrityError:
            # Lost a concurrent create race against uq_active_session_per_table
            # (BR-U4-1). Roll back the failed insert and return the session the
            # winner created, preserving idempotency (BR-U4-2).
            self.db.rollback()
            existing = self.repo.get_active(store_id, table_id)
            if existing is None:
                raise
            return existing.id

    def get_active_session(
        self, store_id: int, table_id: int
    ) -> TableSession | None:
        return self.repo.get_active(store_id, table_id)

    # --- close (US-A6) -----------------------------------------------------
    def close_session(self, store_id: int, table_id: int) -> ClosedSessionSummary:
        session = self.repo.get_active(store_id, table_id)
        if session is None:
            raise NotFoundError("no active session")
        session_id = session.id

        provider = get_order_provider()
        # Contract C: snapshot the live orders (0 orders is valid — BR-U4-5).
        orders = provider.collect_active_session_orders(store_id, session_id)

        total = 0
        for order in orders:
            amount = int(order["order_amount"])
            total += amount
            history = SessionHistoryOrder(
                store_id=store_id,
                session_id=session_id,
                table_id=table_id,
                order_no=order["order_no"],
                order_status=order["order_status"],
                order_amount=amount,
                ordered_at=order["ordered_at"],
            )
            for line in order.get("lines", []):
                history.lines.append(
                    SessionHistoryOrderLine(
                        store_id=store_id,
                        menu_name=line["menu_name"],
                        quantity=int(line["quantity"]),
                        unit_price=int(line["unit_price"]),
                    )
                )
            self.db.add(history)

        closed_at = _now()
        session.total_amount = total
        session.status = "closed"
        session.closed_at = closed_at

        provider.mark_orders_archived(store_id, session_id)
        # Snapshot + finalize + archive commit atomically (BR-U4-4).
        self.db.commit()

        # Best-effort realtime notify after commit (must not break write).
        publish(
            store_id,
            session_closed(
                store_id,
                {
                    "table_id": table_id,
                    "session_id": session_id,
                    "closed_at": closed_at.isoformat(),
                    "total_amount": total,
                },
            ),
        )

        return ClosedSessionSummary(
            table_id=table_id,
            session_id=session_id,
            total_amount=total,
            closed_at=closed_at,
            order_count=len(orders),
        )

    # --- dashboard (US-A5) -------------------------------------------------
    def get_dashboard(
        self, store_id: int, preview_n: int = _DEFAULT_PREVIEW_N
    ) -> list[DashboardCard]:
        if preview_n < 0 or preview_n > _MAX_PREVIEW_N:
            preview_n = _DEFAULT_PREVIEW_N  # BR-U4-16

        provider = get_order_provider()
        table_repo = BaseRepository(self.db, Table)
        sessions = self.repo.list(
            store_id, status="active", limit=_ACTIVE_SCAN_LIMIT
        )

        cards: list[DashboardCard] = []
        for session in sessions:
            table = table_repo.get(store_id, session.table_id)
            orders = provider.collect_active_session_orders(store_id, session.id)
            recent_source = sorted(
                orders, key=lambda o: o["ordered_at"], reverse=True
            )[:preview_n]
            recent = [
                RecentOrder(
                    order_id=o.get("order_id"),
                    order_no=o["order_no"],
                    order_status=o["order_status"],
                    order_amount=int(o["order_amount"]),
                    ordered_at=o["ordered_at"],
                )
                for o in recent_source
            ]
            cards.append(
                DashboardCard(
                    table_id=session.table_id,
                    table_number=table.table_number if table else None,
                    session_id=session.id,
                    total_amount=session.total_amount,
                    started_at=session.started_at,
                    recent_orders=recent,
                )
            )
        return cards

    # --- history (US-A7) ---------------------------------------------------
    def list_history(
        self,
        store_id: int,
        *,
        table_id: int | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Page[HistoryOrderOut]:
        rows, total = self.repo.list_history_orders(
            store_id,
            table_id=table_id,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        )
        items = [
            HistoryOrderOut(
                id=row.id,
                session_id=row.session_id,
                table_id=row.table_id,
                order_no=row.order_no,
                order_status=row.order_status,
                order_amount=row.order_amount,
                ordered_at=row.ordered_at,
                closed_at=row.session.closed_at if row.session else None,
                lines=[
                    HistoryOrderLineOut.model_validate(line)
                    for line in row.lines
                ],
            )
            for row in rows
        ]
        return Page(items=items, total=total, offset=offset, limit=limit)
