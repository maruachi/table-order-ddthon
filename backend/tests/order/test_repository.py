"""U3 OrderRepository tests: numbering, isolation, active filtering."""
from __future__ import annotations

from app.order.models import Order, OrderItem
from app.order.repository import OrderRepository


def _make_order(db, store_id, order_no, session_id=1, table_id=1, total=1000, **kw):
    order = Order(
        store_id=store_id,
        order_no=order_no,
        session_id=session_id,
        table_id=table_id,
        total=total,
        **kw,
    )
    order.items.append(
        OrderItem(
            store_id=store_id,
            menu_id=1,
            menu_name="A",
            unit_price=total,
            qty=1,
            line_total=total,
        )
    )
    db.add(order)
    db.flush()
    return order


def test_next_order_no_is_monotonic_per_store(db):
    repo = OrderRepository(db)
    assert repo.next_order_no(1) == 1
    _make_order(db, 1, 1)
    assert repo.next_order_no(1) == 2
    # independent per store
    assert repo.next_order_no(2) == 1


def test_store_isolation(db):
    repo = OrderRepository(db)
    o1 = _make_order(db, 1, 1)
    _make_order(db, 2, 1)
    assert repo.get(2, o1.id) is None  # cross-tenant fail-closed
    assert repo.get(1, o1.id) is not None


def test_active_filter_excludes_archived_and_deleted(db):
    repo = OrderRepository(db)
    _make_order(db, 1, 1, session_id=10)
    _make_order(db, 1, 2, session_id=10, archived=True)
    _make_order(db, 1, 3, session_id=10, is_deleted=True)
    active = repo.list_active_by_session(1, 10)
    assert {o.order_no for o in active} == {1}
    assert repo.count_active_by_session(1, 10) == 1


def test_sum_active_total_for_table(db):
    repo = OrderRepository(db)
    _make_order(db, 1, 1, table_id=5, total=1000)
    _make_order(db, 1, 2, table_id=5, total=2000)
    _make_order(db, 1, 3, table_id=5, total=500, is_deleted=True)
    assert repo.sum_active_total_for_table(1, 5) == 3000


def test_mark_archived_is_idempotent(db):
    repo = OrderRepository(db)
    o1 = _make_order(db, 1, 1, session_id=10)
    assert repo.mark_archived(1, [o1.id]) == 1
    assert repo.mark_archived(1, [o1.id]) == 0  # already archived
