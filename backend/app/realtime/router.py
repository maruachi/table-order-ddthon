"""Realtime SSE endpoints (U4 Realtime) — US-A2 / US-C6, NFR-1 / NFR-3.

Two Server-Sent-Events streams backed by the in-process :data:`broker`:

* ``GET /realtime/admin/stream`` — kitchen/admin dashboard; receives every event
  for the authenticated store.
* ``GET /realtime/table/stream``  — customer tablet; server-side filtered to the
  authenticated ``table_id`` (Q8=A / BR-U4-10).

Auth (Contract E): browser ``EventSource`` cannot set headers, so the bearer
token is passed as a ``?token=`` query param and verified via ``verify_token``.
Auth failures raise ``AuthError`` (401) / ``ForbiddenError`` (403) and are
translated by the U0 exception handlers.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.common.exceptions import ForbiddenError
from app.common.security import verify_token
from app.realtime.broker import broker

if TYPE_CHECKING:
    from app.realtime.broker import _Subscriber

router = APIRouter(prefix="/realtime", tags=["realtime"])

# Seconds to wait for an event before emitting a keepalive ping (BR-U4-14).
_KEEPALIVE_TIMEOUT = 15

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def _event_stream(
    request: Request, store_id: int, sub: "_Subscriber"
) -> AsyncIterator[str]:
    """Yield SSE frames for ``sub`` until the client disconnects.

    Emits an initial comment frame so clients open immediately, then relays
    events as they arrive. On idle it sends comment pings to keep the connection
    alive; it exits (and unsubscribes) once the client disconnects.
    """
    try:
        yield ": connected\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(
                    sub.queue.get(), timeout=_KEEPALIVE_TIMEOUT
                )
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            yield f"data: {json.dumps(event.to_sse_dict())}\n\n"
    finally:
        broker.unsubscribe(store_id, sub)


@router.get("/admin/stream")
async def admin_stream(
    request: Request, token: str = Query(...)
) -> StreamingResponse:
    ctx = verify_token(token)
    if ctx.role != "admin":
        raise ForbiddenError("admin role required")
    sub = broker.subscribe(ctx.store_id, table_id=None)
    return StreamingResponse(
        _event_stream(request, ctx.store_id, sub),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/table/stream")
async def table_stream(
    request: Request, token: str = Query(...)
) -> StreamingResponse:
    ctx = verify_token(token)
    if ctx.role != "table" or ctx.table_id is None:
        raise ForbiddenError("table role with table binding required")
    # Server-side table filter (Q8=A / BR-U4-10): client cannot widen its scope.
    sub = broker.subscribe(ctx.store_id, table_id=ctx.table_id)
    return StreamingResponse(
        _event_stream(request, ctx.store_id, sub),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
