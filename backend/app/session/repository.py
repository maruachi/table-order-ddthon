"""Session persistence (U4) — store-scoped (NFR-3, BR-U4-3).

``SessionRepository`` extends the U0 ``BaseRepository`` so every query is
isolated by ``store_id``. History reads join ``TableSession`` because ordering
and date filtering are keyed on the owning session's ``closed_at``.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from app.common.repository import BaseRepository
from app.session.models import SessionHistoryOrder, TableSession


def _start_bound(value: date | datetime) -> datetime:
    # ``datetime`` is a subclass of ``date`` — check it first.
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


def _end_bound_exclusive(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    # Whole-day inclusive: closed_at < (date_to + 1 day).
    return datetime.combine(value, time.min) + timedelta(days=1)


class SessionRepository(BaseRepository[TableSession]):
    def __init__(self, db) -> None:
        super().__init__(db, TableSession)

    def get_active(self, store_id: int, table_id: int) -> TableSession | None:
        rows = self.list(store_id, table_id=table_id, status="active", limit=1)
        return rows[0] if rows else None

    def create_active(self, store_id: int, table_id: int) -> TableSession:
        # started_at left to the model's server_default.
        return self.create(
            store_id, table_id=table_id, status="active", total_amount=0
        )

    def list_history_orders(
        self,
        store_id: int,
        *,
        table_id: int | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[SessionHistoryOrder], int]:
        conditions = [
            SessionHistoryOrder.store_id == store_id,
            # Defense-in-depth: scope the joined session by store too, so the
            # read is store-isolated on both tables regardless of write path
            # (BR-U4-3 / NFR-3).
            TableSession.store_id == store_id,
            TableSession.status == "closed",
        ]
        if table_id is not None:
            conditions.append(SessionHistoryOrder.table_id == table_id)
        if date_from is not None:
            conditions.append(TableSession.closed_at >= _start_bound(date_from))
        if date_to is not None:
            conditions.append(
                TableSession.closed_at < _end_bound_exclusive(date_to)
            )

        where = and_(*conditions)
        join_on = SessionHistoryOrder.session_id == TableSession.id

        total_stmt = (
            select(func.count())
            .select_from(SessionHistoryOrder)
            .join(TableSession, join_on)
            .where(where)
        )
        total = int(self.db.scalar(total_stmt) or 0)

        rows_stmt = (
            select(SessionHistoryOrder)
            .join(TableSession, join_on)
            .where(where)
            .options(
                selectinload(SessionHistoryOrder.lines),
                selectinload(SessionHistoryOrder.session),
            )
            .order_by(
                TableSession.closed_at.desc(), SessionHistoryOrder.id.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        rows = self.db.scalars(rows_stmt).all()
        return rows, total
