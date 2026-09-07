"""U4 realtime broker tests: fan-out, tenant/table isolation, thread hand-off.

Exercises ``InMemoryBroker`` (Contract D) and the best-effort ``publish`` helper
in ``app.common.realtime``. ``publish`` marshals queue mutations onto the bound
event loop via ``call_soon_threadsafe`` (NFR-1), so every scenario drives a real
loop with ``run_until_complete`` — awaiting a queue ``get`` flushes the scheduled
offer callbacks. No pytest-asyncio dependency is assumed.
"""
from __future__ import annotations

import asyncio
import threading

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common import realtime as rt
from app.common import security as sec
from app.common.events import SESSION_CLOSED, session_closed
from app.common.exceptions import AuthError, register_exception_handlers
from app.common.security import StoreContext, register_token_verifier
from app.realtime.broker import InMemoryBroker
from app.realtime.router import router as realtime_router


def test_subscribe_publish_basic():
    loop = asyncio.new_event_loop()
    broker = InMemoryBroker()
    broker.bind_loop(loop)

    async def scenario():
        sub = broker.subscribe(1)
        broker.publish(1, session_closed(1, {"table_id": 5}))
        return await asyncio.wait_for(sub.queue.get(), timeout=1)

    try:
        event = loop.run_until_complete(scenario())
    finally:
        loop.close()

    sse = event.to_sse_dict()
    assert sse["type"] == SESSION_CLOSED
    assert sse["store_id"] == 1
    assert sse["payload"]["table_id"] == 5


def test_store_isolation():
    loop = asyncio.new_event_loop()
    broker = InMemoryBroker()
    broker.bind_loop(loop)

    async def scenario():
        sub_a = broker.subscribe(1)
        sub_b = broker.subscribe(2)
        broker.publish(2, session_closed(2, {"table_id": 3}))
        # Awaiting store B's queue flushes all scheduled offers; store A had none.
        event_b = await asyncio.wait_for(sub_b.queue.get(), timeout=1)
        return sub_a.queue.empty(), event_b

    try:
        a_empty, event_b = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert a_empty is True  # BR-U4-10 / NFR-3: cross-tenant events never delivered
    assert event_b.store_id == 2


def test_table_filter():
    loop = asyncio.new_event_loop()
    broker = InMemoryBroker()
    broker.bind_loop(loop)

    async def scenario():
        sub = broker.subscribe(1, table_id=1)
        # Filtered event is published first; if the filter failed it would be
        # first in the queue and get() below would return it.
        broker.publish(1, session_closed(1, {"table_id": 2}))
        broker.publish(1, session_closed(1, {"table_id": 1}))
        event = await asyncio.wait_for(sub.queue.get(), timeout=1)
        return event, sub.queue.empty()

    try:
        event, empty_after = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert event.payload["table_id"] == 1  # Q8=A: only own-table events delivered
    assert empty_after is True


def test_publish_from_thread():
    loop = asyncio.new_event_loop()
    broker = InMemoryBroker()
    broker.bind_loop(loop)

    async def scenario():
        sub = broker.subscribe(1)

        def worker():
            broker.publish(1, session_closed(1, {"table_id": 7}))

        thread = threading.Thread(target=worker)
        thread.start()
        # call_soon_threadsafe wakes the loop from the worker thread (NFR-1).
        event = await asyncio.wait_for(sub.queue.get(), timeout=2)
        thread.join()
        return event

    try:
        event = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert event.payload["table_id"] == 7


def test_publish_helper_is_best_effort():
    class BoomPublisher:
        def publish(self, store_id: int, event) -> None:
            raise RuntimeError("boom")

    original = rt.get_publisher()
    rt.register_publisher(BoomPublisher())
    try:
        # A publisher that raises must not propagate (BR-U4-9 / BR-U0-13).
        assert rt.publish(1, session_closed(1, {"table_id": 1})) is None
    finally:
        rt.register_publisher(original)


def test_unsubscribe_stops_delivery():
    loop = asyncio.new_event_loop()
    broker = InMemoryBroker()
    broker.bind_loop(loop)

    async def scenario():
        sub = broker.subscribe(1)
        broker.unsubscribe(1, sub)
        broker.publish(1, session_closed(1, {"table_id": 1}))
        await asyncio.sleep(0)  # let any scheduled callbacks run
        return sub.queue.empty()

    try:
        empty = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert empty is True


# --- SSE endpoint auth / role / isolation (BR-U4-10 / BR-U4-11) ------------

_ADMIN = StoreContext(store_id=1, role="admin", subject="owner")
_TABLE = StoreContext(store_id=1, role="table", subject="t5", table_id=5)


class _StubVerifier:
    """Maps known tokens to a StoreContext; unknown tokens fail auth."""

    def __init__(self, mapping: dict[str, StoreContext]) -> None:
        self._mapping = mapping

    def verify(self, token: str) -> StoreContext:
        try:
            return self._mapping[token]
        except KeyError:
            raise AuthError("invalid token") from None


@pytest.fixture()
def sse_client():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(realtime_router)

    original = sec._verifier
    register_token_verifier(_StubVerifier({"admin-tok": _ADMIN, "table-tok": _TABLE}))
    try:
        with TestClient(app) as client:
            yield client
    finally:
        sec._verifier = original  # restore global registry (no test leakage)


def test_sse_missing_or_invalid_token_rejected(sse_client):
    # No verifier match -> AuthError -> 401 (BR-U4-11: refuse on failure).
    assert sse_client.get("/realtime/admin/stream", params={"token": "nope"}).status_code == 401
    assert sse_client.get("/realtime/table/stream", params={"token": "nope"}).status_code == 401


def test_sse_role_mismatch_forbidden(sse_client):
    # A table token cannot open the store-wide admin stream, and vice versa.
    assert sse_client.get("/realtime/admin/stream", params={"token": "table-tok"}).status_code == 403
    assert sse_client.get("/realtime/table/stream", params={"token": "admin-tok"}).status_code == 403


class _FakeBroker:
    """Records subscribe() args; avoids opening a real (endless) SSE stream."""

    def __init__(self) -> None:
        self.subscribed: list[tuple[int, int | None]] = []

    def subscribe(self, store_id: int, table_id: int | None = None):
        self.subscribed.append((store_id, table_id))
        return object()

    def unsubscribe(self, store_id: int, sub) -> None:  # pragma: no cover
        pass


class _DummyRequest:
    pass


def test_sse_admin_subscribes_store_wide(monkeypatch):
    import app.realtime.router as router_mod

    fake = _FakeBroker()
    monkeypatch.setattr(router_mod, "broker", fake)
    monkeypatch.setattr(sec, "_verifier", _StubVerifier({"admin-tok": _ADMIN}))

    resp = asyncio.run(router_mod.admin_stream(_DummyRequest(), token="admin-tok"))
    assert resp.status_code == 200
    assert resp.media_type == "text/event-stream"
    # Admin subscribes store-wide (no table filter).
    assert fake.subscribed == [(1, None)]


def test_sse_table_subscribes_with_server_side_filter(monkeypatch):
    import app.realtime.router as router_mod

    fake = _FakeBroker()
    monkeypatch.setattr(router_mod, "broker", fake)
    monkeypatch.setattr(sec, "_verifier", _StubVerifier({"table-tok": _TABLE}))

    resp = asyncio.run(router_mod.table_stream(_DummyRequest(), token="table-tok"))
    assert resp.status_code == 200
    # Q8=A / BR-U4-10: the filter is bound to ctx.table_id, not client input.
    assert fake.subscribed == [(1, 5)]
