"""U1 Auth domain models.

Owns ``AdminUser`` (store-scoped admin login account). ``Store``/``Table`` are
owned by U0 (``app.common.models``); U1 references them but does not redefine
them. Tenant isolation via ``store_id`` FK (NFR-3, BR-U0-1).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base


class AdminUser(Base):
    """Store admin login account. Provisioned by seed only (Q1=A) — no CRUD API."""

    __tablename__ = "admin_users"
    __table_args__ = (
        UniqueConstraint("store_id", "username", name="uq_admin_store_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    # bcrypt hash of the admin password (U0 security.hash_password).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    store: Mapped["Store"] = relationship("Store")  # noqa: F821  (U0 Store)
