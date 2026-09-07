"""U4 Session service tests: lifecycle (Contract B), close-time snapshotting
(Contract C), dashboard (US-A5) and history reads (US-A7).

Mirrors the U0 ``tests/test_common.py`` fixture style: an in-memory SQLite
engine created after importing the model modules so every table is registered
on ``Base.metadata``. Tenant isolation (NFR-3, BR-U4-3) is asserted throughout.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.common.database import Base
from app.common.exceptions import NotFoundError
from app.common.models import Store, Table  # noqa: F401  (register tables)
from app.session.models import (  # noqa: F401  (register tables)
    SessionHistoryOrder,
    SessionHistoryOrderLine,
    TableSession,
)
from app.session.provider import NoOpOrderProvider, register_order_provider
from app.session.service import SessionService


# --- test doubles ----------------------------------------------------------
class MockOrderProvider:
    """Contract C double: returns configured snapshot dicts and records the
    archive call so ``close_session`` behaviour can be asserted."""

    def __init__(self, orders: list[dict[str, Any]] | None = None) -> None:
        self.orders: list[dict[str, Any]] = orders or []
        self.collect_calls: list[tuple[int, int]] = []
        self.archived_calls: list[tuple[int, int]] = []

    def collect_active_session_orders(
        self, store_id: int, session_id: int
    ) -> list[dict[str, Any]]:
        self.collect_calls.append((store_id, session_id))
        return list(self.orders)

    def mark_orders_archived(self, store_id: int, session_id: int) -> None:
        self.archived_calls.append((store_id, session_id))


# --- fixtures --------------------------------------------------------------
@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fixtures(db):
    store_a = Store(code="a", name="A")
    store_b = Store(code="b", name="B")
    db.add_all([store_a, store_b])
    db.flush()
    table_a1 = Table(store_id=store_a.id, table_number="1", password_hash="x")
    table_a2 = Table(store_id=store_a.id, table_number="2", password_hash="x")
    table_b1 = Table(store_id=store_b.id, table_number="1", password_hash="x")
    db.add_all([table_a1, table_a2, table_b1])
    db.flush()
    return SimpleNamespace(
        store_a=store_a,
        store_b=store_b,
        table_a1=table_a1,
        table_a2=table_a2,
        table_b1=table_b1,
    )


@pytest.fixture()
def order_provider():
    """Register a Contract C mock; restore the NoOp default afterwards."""
    provider = MockOrderProvider()
    register_order_provider(provider)
    try:
        yield provider
    finally:
        register_order_provider(NoOpOrderProvider())


@pytest.fixture()
def service(db):
    return SessionService(db)


# --- helpers ---------------------------------------------------------------
def _order(order_no: str, amount: int, ordered_at: datetime, lines=()):
    return {
        "order_no": order_no,
        "order_status": "served",
        "order_amount": amount,
        "ordered_at": ordered_at,
        "lines": list(lines),
    }


def _insert_closed_session(
    db, store_id: int, table_id: int, closed_at: datetime, orders: list[dict]
):
    session = TableSession(
        store_id=store_id,
        table_id=table_id,
        status="closed",
        total_amount=sum(o["order_amount"] for o in orders),
        started_at=closed_at,
        closed_at=closed_at,
    )
    db.add(session)
    db.flush()
    for o in orders:
        history = SessionHistoryOrder(
            store_id=store_id,
            session_id=session.id,
            table_id=table_id,
            order_no=o["order_no"],
            order_status=o["order_status"],
            order_amount=o["order_amount"],
            ordered_at=o["ordered_at"],
        )
        for line in o.get("lines", []):
            history.lines.append(
                SessionHistoryOrderLine(store_id=store_id, **line)
            )
        db.add(history)
    db.flush()
    return session


# --- Contract B: lifecycle -------------------------------------------------
def test_start_or_get_active_session_is_idempotent(service, db, fixtures):
    store_id = fixtures.store_a.id
    table_id = fixtures.table_a1.id

    assert service.get_active_session(store_id, table_id) is None  # None -> ...

    first = service.start_or_get_active_session(store_id, table_id)
    second = service.start_or_get_active_session(store_id, table_id)

    assert first == second  # idempotent (BR-U4-2)
    active = service.get_active_session(store_id, table_id)  # ... -> session
    assert active is not None
    assert active.id == first
    assert active.status == "active"
    # exactly one active session for the table
    count = db.scalar(
        select(func.count())
        .select_from(TableSession)
        .where(
            TableSession.store_id == store_id,
            TableSession.table_id == table_id,
            TableSession.status == "active",
        )
    )
    assert count == 1


def test_partial_unique_blocks_second_active_session(service, db, fixtures):
    """BR-U4-1: DB-level partial unique index rejects a second active row even
    if the service guard were bypassed."""
    store_id = fixtures.store_a.id
    table_id = fixtures.table_a1.id
    service.start_or_get_active_session(store_id, table_id)

    db.add(
        TableSession(
            store_id=store_id, table_id=table_id, status="active", total_amount=0
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


# --- close (US-A6) ---------------------------------------------------------
def test_close_session_snapshots_orders_and_archives(
    service, db, fixtures, order_provider
):
    store_id = fixtures.store_a.id
    table_id = fixtures.table_a1.id
    session_id = service.start_or_get_active_session(store_id, table_id)

    t0 = datetime(2026, 9, 7, 12, 0)
    order_provider.orders = [
        _order(
            "A-1",
            10000,
            t0,
            lines=[
                {"menu_name": "김밥", "quantity": 2, "unit_price": 3000},
                {"menu_name": "라면", "quantity": 1, "unit_price": 4000},
            ],
        ),
        _order(
            "A-2",
            5000,
            t0 + timedelta(minutes=5),
            lines=[{"menu_name": "콜라", "quantity": 5, "unit_price": 1000}],
        ),
    ]

    summary = service.close_session(store_id, table_id)

    assert summary.session_id == session_id
    assert summary.table_id == table_id
    assert summary.total_amount == 15000  # sum of order amounts
    assert summary.order_count == 2
    assert summary.closed_at is not None

    # snapshot rows persisted
    n_orders = db.scalar(
        select(func.count())
        .select_from(SessionHistoryOrder)
        .where(SessionHistoryOrder.store_id == store_id)
    )
    n_lines = db.scalar(
        select(func.count())
        .select_from(SessionHistoryOrderLine)
        .where(SessionHistoryOrderLine.store_id == store_id)
    )
    assert n_orders == 2
    assert n_lines == 3

    # session finalized
    closed = db.get(TableSession, session_id)
    assert closed.status == "closed"
    assert closed.closed_at is not None
    assert closed.total_amount == 15000

    # Contract C archive callback invoked with the right scope
    assert order_provider.archived_calls == [(store_id, session_id)]

    # no active session remains
    assert service.get_active_session(store_id, table_id) is None


def test_close_session_with_zero_orders_still_closes(
    service, db, fixtures, order_provider
):
    """BR-U4-5: a session with no orders closes normally (order_count=0)."""
    store_id = fixtures.store_a.id
    table_id = fixtures.table_a1.id
    session_id = service.start_or_get_active_session(store_id, table_id)
    order_provider.orders = []

    summary = service.close_session(store_id, table_id)

    assert summary.order_count == 0
    assert summary.total_amount == 0
    closed = db.get(TableSession, session_id)
    assert closed.status == "closed"
    assert closed.closed_at is not None
    assert order_provider.archived_calls == [(store_id, session_id)]


def test_close_session_without_active_raises_not_found(
    service, fixtures, order_provider
):
    with pytest.raises(NotFoundError):
        service.close_session(fixtures.store_a.id, fixtures.table_a1.id)


# --- tenant isolation (BR-U4-3, NFR-3) -------------------------------------
def test_store_isolation_on_get_and_close(service, fixtures, order_provider):
    """Store A's active session is invisible / not closable via store B
    (fail-closed)."""
    store_a = fixtures.store_a.id
    store_b = fixtures.store_b.id
    table_id = fixtures.table_a1.id
    service.start_or_get_active_session(store_a, table_id)

    # B cannot see A's session (even reusing A's table_id)
    assert service.get_active_session(store_b, table_id) is None
    # B cannot close A's session
    with pytest.raises(NotFoundError):
        service.close_session(store_b, table_id)
    # A's session is untouched
    assert service.get_active_session(store_a, table_id) is not None


# --- history (US-A7) -------------------------------------------------------
def test_list_history_ordering_filters_and_page(service, db, fixtures):
    store_a = fixtures.store_a.id
    t1 = fixtures.table_a1.id
    t2 = fixtures.table_a2.id

    _insert_closed_session(
        db, store_a, t1, datetime(2026, 9, 1, 12, 0),
        [_order("H1", 1000, datetime(2026, 9, 1, 11, 0))],
    )
    _insert_closed_session(
        db, store_a, t1, datetime(2026, 9, 3, 12, 0),
        [
            _order(
                "H2",
                2000,
                datetime(2026, 9, 3, 11, 0),
                lines=[
                    {"menu_name": "밥", "quantity": 1, "unit_price": 1000},
                    {"menu_name": "국", "quantity": 1, "unit_price": 1000},
                ],
            )
        ],
    )
    _insert_closed_session(
        db, store_a, t2, datetime(2026, 9, 5, 12, 0),
        [_order("H3", 3000, datetime(2026, 9, 5, 11, 0))],
    )

    # full list: closed_at descending
    page = service.list_history(store_a)
    assert [i.order_no for i in page.items] == ["H3", "H2", "H1"]
    assert page.total == 3
    assert page.offset == 0
    assert page.limit == 50
    # closed_at + lines mapped through
    h2 = next(i for i in page.items if i.order_no == "H2")
    assert h2.closed_at == datetime(2026, 9, 3, 12, 0)
    assert len(h2.lines) == 2

    # table filter
    page_t1 = service.list_history(store_a, table_id=t1)
    assert [i.order_no for i in page_t1.items] == ["H2", "H1"]
    assert page_t1.total == 2

    # date filter is keyed on closed_at (Q6=A): [9/2, 9/4] -> only H2 (9/3)
    page_date = service.list_history(
        store_a, date_from=date(2026, 9, 2), date_to=date(2026, 9, 4)
    )
    assert [i.order_no for i in page_date.items] == ["H2"]
    assert page_date.total == 1

    # tenant isolation: store B sees nothing
    page_b = service.list_history(fixtures.store_b.id)
    assert page_b.items == []
    assert page_b.total == 0


# --- dashboard (US-A5) -----------------------------------------------------
def test_get_dashboard_cards_and_preview_limit(
    service, fixtures, order_provider
):
    store_a = fixtures.store_a.id
    table_id = fixtures.table_a1.id
    session_id = service.start_or_get_active_session(store_a, table_id)

    base = datetime(2026, 9, 7, 10, 0)
    order_provider.orders = [
        _order(f"D{i}", 1000 * i, base + timedelta(minutes=i)) for i in range(1, 6)
    ]

    cards = service.get_dashboard(store_a, preview_n=3)
    assert len(cards) == 1
    card = cards[0]
    assert card.table_id == table_id
    assert card.table_number == "1"
    assert card.session_id == session_id
    # preview limited to 3, most recent first (ordered_at desc)
    assert [o.order_no for o in card.recent_orders] == ["D5", "D4", "D3"]


def test_get_dashboard_negative_preview_resets_to_default(
    service, fixtures, order_provider
):
    """BR-U4-16: out-of-range preview_n is reset to the default (3)."""
    store_a = fixtures.store_a.id
    service.start_or_get_active_session(store_a, fixtures.table_a1.id)
    base = datetime(2026, 9, 7, 10, 0)
    order_provider.orders = [
        _order(f"D{i}", 1000, base + timedelta(minutes=i)) for i in range(1, 6)
    ]

    negative = service.get_dashboard(store_a, preview_n=-1)
    assert len(negative[0].recent_orders) == 3

    over_max = service.get_dashboard(store_a, preview_n=999)
    assert len(over_max[0].recent_orders) == 3
