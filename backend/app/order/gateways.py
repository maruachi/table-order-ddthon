"""Cross-unit contract gateways for U3 (Contracts A & B).

U3 depends on U2 (menu lookup) and U4 (session lifecycle). To enable parallel
development (Q6-B), those dependencies are expressed as ``Protocol`` interfaces
here and injected into ``OrderService``. Stubs are provided so U3 runs and tests
independently; at integration the real U2/U4 implementations are injected.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MenuItemInfo:
    """Contract A result row: authoritative menu id/name/price/availability."""

    id: int
    name: str
    price: int
    available: bool


class MenuLookup(Protocol):
    """Contract A (U3 -> U2): validate menus and fetch authoritative prices."""

    def get_menu_items(
        self, store_id: int, menu_ids: list[int]
    ) -> list[MenuItemInfo]: ...


class SessionGateway(Protocol):
    """Contract B (U3 -> U4): table session lifecycle access."""

    def start_or_get_active_session(self, store_id: int, table_id: int) -> int:
        """Return the active session id, starting a new session if needed."""
        ...

    def get_active_session(self, store_id: int, table_id: int) -> int | None:
        """Return the active session id, or None if no active session."""
        ...


# --- stubs (parallel dev / tests) ----------------------------------------
class StubMenuLookup:
    """Deterministic stub: echoes requested ids as available items.

    Replaced by the real U2 MenuService at integration.
    """

    def __init__(self, catalog: dict[int, MenuItemInfo] | None = None):
        # When an explicit catalog is given it is authoritative: unknown ids are
        # simply not returned (menu not found). With no catalog, ids are echoed
        # as available items for standalone dev runs.
        self._catalog = catalog
        self._strict = catalog is not None

    def get_menu_items(self, store_id: int, menu_ids: list[int]) -> list[MenuItemInfo]:
        result: list[MenuItemInfo] = []
        for mid in menu_ids:
            if self._strict:
                info = self._catalog.get(mid)
                if info is not None:
                    result.append(info)
            else:
                # default: available item priced at 1000 * id (dev only)
                result.append(
                    MenuItemInfo(id=mid, name=f"메뉴 {mid}", price=1000 * mid, available=True)
                )
        return result


class StubSessionGateway:
    """In-memory session stub keyed by (store_id, table_id).

    Replaced by the real U4 SessionService at integration.
    """

    def __init__(self) -> None:
        self._sessions: dict[tuple[int, int], int] = {}
        self._seq = 0

    def start_or_get_active_session(self, store_id: int, table_id: int) -> int:
        key = (store_id, table_id)
        if key not in self._sessions:
            self._seq += 1
            self._sessions[key] = self._seq
        return self._sessions[key]

    def get_active_session(self, store_id: int, table_id: int) -> int | None:
        return self._sessions.get((store_id, table_id))
