"""Order API router (U3).

Endpoints for customer (table role) and admin. Store isolation & roles are
enforced via U0 dependencies. Cross-unit gateways (Contract A/B) are provided
through ``get_menu_lookup`` / ``get_session_gateway`` which are overridden with
real U2/U4 implementations at integration.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.common.schemas import Page, PageParams
from app.common.security import (
    StoreContext,
    get_current_store_context,
    require_admin,
    require_table,
)
from app.order.gateways import (
    MenuLookup,
    SessionGateway,
    StubMenuLookup,
    StubSessionGateway,
)
from app.order.schemas import (
    OrderDetailOut,
    OrderInput,
    OrderOut,
    StatusUpdateIn,
    TableCard,
    TableTotals,
)
from app.order.service import OrderService

router = APIRouter(prefix="/orders", tags=["order"])

# --- gateway providers (overridden at integration with real U2/U4) -------
_menu_lookup: MenuLookup = StubMenuLookup()
_session_gateway: SessionGateway = StubSessionGateway()


def get_menu_lookup() -> MenuLookup:
    return _menu_lookup


def get_session_gateway() -> SessionGateway:
    return _session_gateway


def set_gateways(menu_lookup: MenuLookup, session_gateway: SessionGateway) -> None:
    """Integration hook: inject real U2/U4 implementations."""
    global _menu_lookup, _session_gateway
    _menu_lookup = menu_lookup
    _session_gateway = session_gateway


def get_order_service(
    db: Session = Depends(get_db),
    menu_lookup: MenuLookup = Depends(get_menu_lookup),
    session_gateway: SessionGateway = Depends(get_session_gateway),
) -> OrderService:
    return OrderService(db, menu_lookup, session_gateway)


# --- customer (table) -----------------------------------------------------
@router.post("", response_model=OrderDetailOut, status_code=201)
def create_order(
    payload: OrderInput,
    ctx: StoreContext = Depends(require_table),
    service: OrderService = Depends(get_order_service),
):
    order = service.create_order(ctx, payload.items)
    service.db.commit()
    return service.repo.get_with_items(ctx.store_id, order.id)


@router.get("/current", response_model=Page[OrderOut])
def list_current_orders(
    page: PageParams = Depends(),
    ctx: StoreContext = Depends(require_table),
    service: OrderService = Depends(get_order_service),
):
    orders, total = service.list_current_session_orders(ctx, page.offset, page.limit)
    return Page(items=orders, total=total, offset=page.offset, limit=page.limit)


# --- admin ----------------------------------------------------------------
@router.get("/dashboard", response_model=list[TableCard])
def dashboard_snapshot(
    table_id: int | None = Query(default=None),
    ctx: StoreContext = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
):
    return service.get_dashboard_snapshot(ctx, table_filter=table_id)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int,
    payload: StatusUpdateIn,
    ctx: StoreContext = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
):
    order = service.update_order_status(ctx, order_id, payload.status.value)
    service.db.commit()
    return order


@router.delete("/{order_id}", response_model=TableTotals)
def delete_order(
    order_id: int,
    ctx: StoreContext = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
):
    totals = service.delete_order(ctx, order_id)
    service.db.commit()
    return totals


# --- shared (table own-session / admin) -----------------------------------
@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(
    order_id: int,
    ctx: StoreContext = Depends(get_current_store_context),
    service: OrderService = Depends(get_order_service),
):
    return service.get_order(ctx, order_id)
