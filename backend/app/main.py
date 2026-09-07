"""FastAPI application assembly (U0 Platform/Common).

Wires CORS, exception handlers, DB init, and domain routers. Domain units add
their routers + register their token verifier (U1) / realtime broker (U4) here
as they land.
"""
from __future__ import annotations

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
    # Domain units register integrations at startup, e.g.:
    #   from app.auth.verifier import JwtTokenVerifier
    #   from app.common.security import register_token_verifier
    #   register_token_verifier(JwtTokenVerifier())
    #   from app.realtime.broker import InMemoryBroker
    #   from app.common.realtime import register_publisher
    #   register_publisher(InMemoryBroker())
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

    # Domain routers are included as units land, e.g.:
    #   from app.auth.router import router as auth_router
    #   app.include_router(auth_router)
    from app.menu.router import router as menu_router  # U2 Menu

    app.include_router(menu_router)
    return app


app = create_app()
