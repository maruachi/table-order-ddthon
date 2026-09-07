"""U3 OrderService tests using stub gateways (Contracts A/B mocked)."""
from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.common.security import StoreContext
from app.order.gateways import MenuItemInfo, StubMenuLookup, StubSessionGateway
from app.order.schemas import OrderItemIn
from app.order.service import OrderService

CATALOG = {
    1: MenuItemInfo(id=1, name="아메리카노", price=4000, available=True),
    2: MenuItemInfo(id=2, name="라떼", price=5000, available=True),
    3: MenuItemInfo(id=3, name="품절메뉴", price=3000, available=False),
}


def _service(db):
    return OrderService(db, StubMenuLookup(CATALOG), StubSessionGateway())


def _table_ctx(store_id=1, table_id=7):
    return StoreContext(store_id=store_id, role="table", subject="t7", table_id=table_id)


def _admin_ctx(store_id=1):
    return StoreContext(store_id=store_id, role="admin", subject="owner")


def test_create_order_computes_total_and_snapshots(db):
    svc = _service(db)
    order = svc.create_order(_table_ctx(), [OrderItemIn(menu_id=1, qty=2), OrderItemIn(menu_id=2, qty=1)])
    db.flush()
    assert order.total == 4000 * 2 + 5000
    assert order.order_no == 1
    assert order.status == "pending"
    assert order.session_id is not None
    names = {i.menu_name for i in order.items}
    assert names == {"아메리카노", "라떼"}


def test_create_order_empty_rejected(db):
    svc = _service(db)
    with pytest.raises(ValidationError):
        svc.create_order(_table_ctx(), [])


def test_create_order_unavailable_menu_rejected(db):
    svc = _service(db)
    with pytest.raises(ValidationError):
        svc.create_order(_table_ctx(), [OrderItemIn(menu_id=3, qty=1)])


def test_create_order_unknown_menu_rejected(db):
    svc = OrderService(db, StubMenuLookup(CATALOG), StubSessionGateway())
    with pytest.raises(ValidationError):
        # StubMenuLookup only returns ids it knows when catalog provided
        svc.create_order(_table_ctx(), [OrderItemIn(menu_id=999, qty=1)])


def test_current_session_orders_isolated(db):
    svc = _service(db)
    ctx = _table_ctx()
    svc.create_order(ctx, [OrderItemIn(menu_id=1, qty=1)])
    svc.create_order(ctx, [OrderItemIn(menu_id=2, qty=1)])
    db.flush()
    orders, total = svc.list_current_session_orders(ctx)
    assert total == 2
    assert len(orders) == 2


def test_status_free_transition_and_event(db):
    svc = _service(db)
    ctx = _table_ctx()
    order = svc.create_order(ctx, [OrderItemIn(menu_id=1, qty=1)])
    db.flush()
    updated = svc.update_order_status(_admin_ctx(), order.id, "done")
    assert updated.status == "done"
    # invalid status rejected
    with pytest.raises(ValidationError):
        svc.update_order_status(_admin_ctx(), order.id, "bogus")


def test_soft_delete_recomputes_total(db):
    svc = _service(db)
    ctx = _table_ctx()
    o1 = svc.create_order(ctx, [OrderItemIn(menu_id=1, qty=1)])  # 4000
    svc.create_order(ctx, [OrderItemIn(menu_id=2, qty=1)])  # 5000
    db.flush()
    totals = svc.delete_order(_admin_ctx(), o1.id)
    assert totals["total"] == 5000
    with pytest.raises(NotFoundError):
        svc.get_order(_admin_ctx(), o1.id)


def test_contract_c_collect_and_archive(db):
    svc = _service(db)
    ctx = _table_ctx()
    o1 = svc.create_order(ctx, [OrderItemIn(menu_id=1, qty=1)])
    session_id = o1.session_id
    db.flush()
    collected = svc.collect_active_session_orders(ctx.store_id, session_id)
    assert len(collected) == 1
    assert svc.mark_orders_archived(ctx.store_id, [o1.id]) == 1
    # after archive, current session list is empty
    orders, total = svc.list_current_session_orders(ctx)
    assert total == 0 and orders == []
