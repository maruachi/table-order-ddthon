"""Realtime event schema (U0) — Contract D single source of truth.

Publishers (U3 Order, U4 Session) build events via the factory helpers; the SSE
broker (U4) and subscribers consume the same schema.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Event type constants
ORDER_CREATED = "order.created"
ORDER_UPDATED = "order.updated"
ORDER_STATUS_CHANGED = "order.status_changed"
ORDER_DELETED = "order.deleted"
SESSION_CLOSED = "session.closed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Event:
    type: str
    store_id: int
    payload: dict[str, Any] = field(default_factory=dict)
    ts: datetime = field(default_factory=_now)

    def to_sse_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "store_id": self.store_id,
            "payload": self.payload,
            "ts": self.ts.isoformat(),
        }


# --- factory helpers ------------------------------------------------------
def order_created(store_id: int, payload: dict[str, Any]) -> Event:
    return Event(ORDER_CREATED, store_id, payload)


def order_updated(store_id: int, payload: dict[str, Any]) -> Event:
    return Event(ORDER_UPDATED, store_id, payload)


def order_status_changed(store_id: int, payload: dict[str, Any]) -> Event:
    return Event(ORDER_STATUS_CHANGED, store_id, payload)


def order_deleted(store_id: int, payload: dict[str, Any]) -> Event:
    return Event(ORDER_DELETED, store_id, payload)


def session_closed(store_id: int, payload: dict[str, Any]) -> Event:
    return Event(SESSION_CLOSED, store_id, payload)
