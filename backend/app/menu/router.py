"""U2 Menu API layer.

Customer read (``require_table``) and admin management (``require_admin``).
store_id always comes from the authenticated StoreContext, never the client
(BR-U0-3). Pydantic validates input at this boundary; the service raises typed
AppErrors that U0's central handler renders.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.common.security import StoreContext, require_admin, require_table
from app.menu.schemas import (
    AvailabilityInput,
    CategoryInput,
    CategoryOut,
    CategoryWithMenus,
    MenuInput,
    MenuOut,
    ReorderInput,
)
from app.menu.service import MenuService

router = APIRouter(tags=["menu"])


def _service(db: Session = Depends(get_db)) -> MenuService:
    return MenuService(db)


# --- customer -------------------------------------------------------------


@router.get("/api/menu", response_model=list[CategoryWithMenus])
def get_menu(
    ctx: StoreContext = Depends(require_table),
    svc: MenuService = Depends(_service),
) -> list[CategoryWithMenus]:
    """Grouped-by-category menu for the customer screen (US-C2)."""
    return svc.list_menus_for_customer(ctx.store_id)


# --- admin: categories ----------------------------------------------------


@router.get("/api/admin/categories", response_model=list[CategoryOut])
def list_categories(
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.list_categories(ctx.store_id)


@router.post("/api/admin/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.create_category(ctx.store_id, payload.name)


@router.put("/api/admin/categories/reorder", status_code=204)
def reorder_categories(
    payload: ReorderInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    svc.reorder_categories(ctx.store_id, payload.ordered_ids)


@router.put("/api/admin/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.update_category(ctx.store_id, category_id, payload.name)


@router.delete("/api/admin/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    svc.delete_category(ctx.store_id, category_id)


# --- admin: menus ---------------------------------------------------------


@router.get("/api/admin/menus", response_model=list[MenuOut])
def list_menus(
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.list_menus_admin(ctx.store_id)


@router.post("/api/admin/menus", response_model=MenuOut, status_code=201)
def create_menu(
    payload: MenuInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.create_menu(
        ctx.store_id,
        category_id=payload.category_id,
        name=payload.name,
        price=payload.price,
        description=payload.description,
        image_url=str(payload.image_url) if payload.image_url else None,
    )


@router.put("/api/admin/menus/reorder", status_code=204)
def reorder_menus(
    category_id: int,
    payload: ReorderInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    """Reorder menus within a category. ``category_id`` is a query param."""
    svc.reorder_menus(ctx.store_id, category_id, payload.ordered_ids)


@router.put("/api/admin/menus/{menu_id}", response_model=MenuOut)
def update_menu(
    menu_id: int,
    payload: MenuInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.update_menu(
        ctx.store_id,
        menu_id,
        category_id=payload.category_id,
        name=payload.name,
        price=payload.price,
        description=payload.description,
        image_url=str(payload.image_url) if payload.image_url else None,
    )


@router.put("/api/admin/menus/{menu_id}/availability", response_model=MenuOut)
def set_menu_availability(
    menu_id: int,
    payload: AvailabilityInput,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    return svc.set_menu_availability(ctx.store_id, menu_id, payload.available)


@router.delete("/api/admin/menus/{menu_id}", status_code=204)
def delete_menu(
    menu_id: int,
    ctx: StoreContext = Depends(require_admin),
    svc: MenuService = Depends(_service),
):
    svc.delete_menu(ctx.store_id, menu_id)
