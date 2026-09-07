"""Integration adapters wiring U3 Order to the real U2 (menu) and U4 (session).

The order router declares Contract A/B gateways via ``get_menu_lookup`` /
``get_session_gateway`` and ships with stub implementations for standalone dev
and tests. At application assembly (``main.create_app``) these providers are
overridden with the adapters below so orders validate against real menus and
attach to the real table session.

Both adapters take the per-request ``Session`` from U0 ``get_db``. Because
FastAPI caches ``get_db`` within a request, the MenuService/SessionService here
share the exact same ``Session`` as the ``OrderService`` — so a session started
by ``start_or_get_active_session`` is committed atomically by the order router's
``service.db.commit()``.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.menu.service import MenuService
from app.order.gateways import MenuItemInfo
from app.session.service import SessionService


class MenuServiceLookup:
    """Contract A adapter over U2 ``MenuService.get_menu_items`` (dict -> dataclass)."""

    def __init__(self, db: Session):
        self._menu = MenuService(db)

    def get_menu_items(self, store_id: int, menu_ids: list[int]) -> list[MenuItemInfo]:
        rows = self._menu.get_menu_items(store_id, menu_ids)
        return [
            MenuItemInfo(
                id=row["id"],
                name=row["name"],
                price=row["price"],
                available=row["available"],
            )
            for row in rows
        ]


class SessionServiceGateway:
    """Contract B adapter over U4 ``SessionService`` (returns bare session ids)."""

    def __init__(self, db: Session):
        self._sessions = SessionService(db)

    def start_or_get_active_session(self, store_id: int, table_id: int) -> int:
        return self._sessions.start_or_get_active_session(store_id, table_id)

    def get_active_session(self, store_id: int, table_id: int) -> int | None:
        session = self._sessions.get_active_session(store_id, table_id)
        return session.id if session is not None else None


def provide_menu_lookup(db: Session = Depends(get_db)) -> MenuServiceLookup:
    return MenuServiceLookup(db)


def provide_session_gateway(db: Session = Depends(get_db)) -> SessionServiceGateway:
    return SessionServiceGateway(db)
