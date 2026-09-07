"""Order-history provider contract (Contract C) — decoupling registry.

U3 (Order) implements ``OrderHistoryProvider`` and registers it at startup so
U4 can collect a session's live orders at close time and mark them archived,
without a direct U4->U3 import dependency. Until U3 registers (and in tests /
standalone dev), ``NoOpOrderProvider`` is used (empty order list, BR-U4-5).

Mirrors the ``register_publisher`` / ``get_publisher`` pattern in
``app.common.realtime``.
"""
from __future__ import annotations

from typing import Any, Protocol


class OrderHistoryProvider(Protocol):
    """Implemented by U3 Order; consumed by U4 at session close / dashboard."""

    def collect_active_session_orders(
        self, store_id: int, session_id: int
    ) -> list[dict[str, Any]]:
        """Return this session's orders as snapshot dicts.

        Each dict: ``{order_no, order_status, order_amount: int,
        ordered_at: datetime, lines: [{menu_name, quantity: int,
        unit_price: int}]}``.
        """
        ...

    def mark_orders_archived(self, store_id: int, session_id: int) -> None:
        """Flag the session's orders as archived once snapshotted."""
        ...


class NoOpOrderProvider:
    """Default provider: no orders, archiving is a no-op."""

    def collect_active_session_orders(
        self, store_id: int, session_id: int
    ) -> list[dict[str, Any]]:  # noqa: D102
        return []

    def mark_orders_archived(self, store_id: int, session_id: int) -> None:  # noqa: D102
        return None


_provider: OrderHistoryProvider = NoOpOrderProvider()


def register_order_provider(provider: OrderHistoryProvider) -> None:
    """Called by U3 at startup to plug in the real order-history provider."""
    global _provider
    _provider = provider


def get_order_provider() -> OrderHistoryProvider:
    return _provider
