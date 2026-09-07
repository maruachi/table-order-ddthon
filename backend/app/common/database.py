"""Database layer (U0 Platform/Common).

Synchronous SQLAlchemy engine + session factory + declarative Base.
Schema is created via ``init_db()`` using ``create_all`` (no Alembic) per the
approved tech decisions. NFR-4 (persistence).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.common.config import settings

# SQLite needs check_same_thread=False for use across FastAPI's threadpool.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base shared by all unit models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Non-destructive (existing tables preserved).

    Importing model modules registers them on ``Base.metadata``. Domain units
    add their models here as they land.
    """
    # Import models so they are registered on Base.metadata before create_all.
    from app.common import models  # noqa: F401  (Store, Table)
    from app.auth import models as _auth_models  # noqa: F401  (AdminUser)
    from app.session import models as _session_models  # noqa: F401  (U4)

    # NOTE: domain units register their models by importing them here, e.g.:
    #   from app.menu import models as _menu_models   # noqa: F401
    # (added when each unit lands)
    from app.order import models as _order_models  # noqa: F401  (U3: Order, OrderItem)

    Base.metadata.create_all(bind=engine)
