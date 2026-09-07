"""In-memory realtime broker (U4 Realtime) — Contract D, NFR-1.

Implements the U0 ``RealtimePublisher`` protocol (``publish(store_id, event)``)
as a per-store in-memory pub-sub fan-out over ``asyncio.Queue`` subscribers.

Threading model: SSE subscribers are created and consumed inside the FastAPI
event loop (async endpoints), while ``publish`` may be invoked from the
synchronous request threadpool (domain services run under sync SQLAlchemy). We
therefore never touch asyncio objects from a worker thread directly — ``publish``
marshals every queue mutation back onto the captured event loop via
``call_soon_threadsafe`` and never raises (best-effort, BR-U0-13, NFR-1).

Multi-tenancy (NFR-3): every subscriber and event is scoped by ``store_id``.
Customer (table) streams additionally filter by ``table_id`` server-side
(Q8=A / BR-U4-10).
"""
from __future__ import annotations

import asyncio
import logging

from app.common.events import Event

logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 1000


class _Subscriber:
    """A single SSE subscriber: a bounded queue + optional table filter."""

    __slots__ = ("queue", "table_id")

    def __init__(self, queue: "asyncio.Queue[Event]", table_id: int | None) -> None:
        self.queue = queue
        self.table_id = table_id


class InMemoryBroker:
    """Per-store in-memory pub-sub implementing ``RealtimePublisher`` (Contract D)."""

    def __init__(self) -> None:
        self._subs: dict[int, set[_Subscriber]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the event loop used to marshal cross-thread queue puts."""
        self._loop = loop

    def subscribe(self, store_id: int, table_id: int | None = None) -> _Subscriber:
        """Register a new subscriber for ``store_id`` (optionally table-filtered).

        Called from an async endpoint, so lazily capture the running loop if it
        was not already bound at startup.
        """
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:  # pragma: no cover - defensive
                logger.warning("subscribe called without a running event loop")
        sub = _Subscriber(asyncio.Queue(maxsize=_QUEUE_MAXSIZE), table_id)
        self._subs.setdefault(store_id, set()).add(sub)
        return sub

    def unsubscribe(self, store_id: int, sub: _Subscriber) -> None:
        """Remove a subscriber; drop the store bucket once it is empty."""
        subs = self._subs.get(store_id)
        if not subs:
            return
        subs.discard(sub)
        if not subs:
            self._subs.pop(store_id, None)

    def publish(self, store_id: int, event: Event) -> None:
        """Fan out ``event`` to all matching subscribers of ``store_id``.

        Safe to call from a worker thread: queue mutation is always marshaled
        back onto the event loop. This method never raises.
        """
        try:
            subs = self._subs.get(store_id)
            if not subs:
                return
            loop = self._loop
            if loop is None:  # pragma: no cover - defensive
                logger.warning("publish before event loop bound store=%s", store_id)
                return
            event_table_id = event.payload.get("table_id")
            for sub in tuple(subs):
                # Server-side table filter for customer streams (BR-U4-10).
                if sub.table_id is not None and event_table_id != sub.table_id:
                    continue
                loop.call_soon_threadsafe(self._offer, sub, event)
        except Exception:  # pragma: no cover - realtime must never break writes
            logger.exception(
                "broker publish failed store=%s type=%s", store_id, event.type
            )

    @staticmethod
    def _offer(sub: _Subscriber, event: Event) -> None:
        """Enqueue on the event loop; drop the oldest item on backpressure."""
        queue = sub.queue
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            try:
                queue.get_nowait()  # drop oldest to bound memory
            except asyncio.QueueEmpty:  # pragma: no cover - race
                pass
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover - race
                pass


# Module-level singleton shared by main.py (register_publisher) and router.py.
broker = InMemoryBroker()
