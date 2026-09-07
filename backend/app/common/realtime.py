"""Realtime publisher contract (U0) — Contract D.

U0 defines the ``RealtimePublisher`` protocol and a registry. U4 registers the
real per-store in-memory pub-sub broker at startup. Until then (and in tests),
a ``NoOpPublisher`` is used so U3/U4 can develop against the contract in
parallel. Publishing is best-effort and must not break the main transaction
(BR-U0-13).
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.common.events import Event

logger = logging.getLogger(__name__)


class RealtimePublisher(Protocol):
    def publish(self, store_id: int, event: Event) -> None: ...


class NoOpPublisher:
    """Default publisher: logs at debug level, does nothing else."""

    def publish(self, store_id: int, event: Event) -> None:  # noqa: D102
        logger.debug("NoOpPublisher drop event store=%s type=%s", store_id, event.type)


_publisher: RealtimePublisher = NoOpPublisher()


def register_publisher(publisher: RealtimePublisher) -> None:
    """Called by U4 at startup to plug in the real broker."""
    global _publisher
    _publisher = publisher


def get_publisher() -> RealtimePublisher:
    return _publisher


def publish(store_id: int, event: Event) -> None:
    """Best-effort publish helper for domain services to call."""
    try:
        _publisher.publish(store_id, event)
    except Exception:  # pragma: no cover - realtime must never break writes
        logger.exception("realtime publish failed store=%s type=%s", store_id, event.type)
