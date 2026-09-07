"""U4 Session HTTP API (admin-only).

Exposes the dashboard (US-A5), session close (US-A6) and order history
(US-A7). ``store_id`` is always taken from the authenticated ``StoreContext``
and never from client input (BR-U4-3). Pagination follows the U0 ``PageParams``
contract (offset>=0, 1<=limit<=200).
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.common.schemas import Page
from app.common.security import StoreContext, require_admin
from app.session.schemas import (
    ClosedSessionSummary,
    CloseSessionRequest,
    DashboardCard,
    HistoryOrderOut,
)
from app.session.service import SessionService

router = APIRouter(prefix="/sessions", tags=["session"])


@router.get("/dashboard", response_model=list[DashboardCard])
def get_dashboard(
    preview_n: int = Query(default=3),
    ctx: StoreContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[DashboardCard]:
    return SessionService(db).get_dashboard(ctx.store_id, preview_n)


@router.post("/close", response_model=ClosedSessionSummary)
def close_session(
    body: CloseSessionRequest,
    ctx: StoreContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ClosedSessionSummary:
    return SessionService(db).close_session(ctx.store_id, body.table_id)


@router.get("/history", response_model=Page[HistoryOrderOut])
def list_history(
    table_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    ctx: StoreContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[HistoryOrderOut]:
    return SessionService(db).list_history(
        ctx.store_id,
        table_id=table_id,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )
