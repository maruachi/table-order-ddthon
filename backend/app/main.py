"""FastAPI application assembly (U0 Platform/Common).

Wires CORS, exception handlers, DB init, and domain routers. Domain units add
their routers + register their token verifier (U1) / realtime broker (U4) here
as they land.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.common.database import init_db
from app.common.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create schema on startup (create_all; non-destructive).
    init_db()
    # U1 Auth registers the token verifier (Contract E).
    from app.auth.tokens import JwtTokenVerifier
    from app.common.security import register_token_verifier

    register_token_verifier(JwtTokenVerifier())
    # U4 Realtime: bind the running event loop and register the broker as the
    # in-process RealtimePublisher (Contract D). The router subscribes on the
    # same module singleton.
    from app.realtime.broker import broker
    from app.common.realtime import register_publisher

    broker.bind_loop(asyncio.get_running_loop())
    register_publisher(broker)
    # U3 integration (Contract C): register the real order-history provider so
    # U4's dashboard preview and session-close snapshot see live U3 orders.
    from app.order.history_provider import OrderHistoryProviderImpl
    from app.session.provider import register_order_provider

    register_order_provider(OrderHistoryProviderImpl())
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Table Order Service", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["platform"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Domain routers are included as units land.
    from app.auth.router import router as auth_router
    from app.menu.router import router as menu_router  # U2 Menu
    from app.order.router import router as order_router  # U3
    from app.session.router import router as session_router  # U4
    from app.realtime.router import router as realtime_router  # U4

    app.include_router(auth_router)
    app.include_router(menu_router)
    app.include_router(order_router)
    app.include_router(session_router)
    app.include_router(realtime_router)

    # U3 integration: replace the order router's stub Contract A/B gateways with
    # real U2 (menu) / U4 (session) adapters sharing the per-request DB session.
    from app.order.router import get_menu_lookup, get_session_gateway
    from app.order.integration import provide_menu_lookup, provide_session_gateway

    app.dependency_overrides[get_menu_lookup] = provide_menu_lookup
    app.dependency_overrides[get_session_gateway] = provide_session_gateway
    return app


app = create_app()
