"""Security & tenant context (U0) — Contract E.

Provides the request-scoped ``StoreContext``, a pluggable ``TokenVerifier``
registry (implemented by U1 Auth to avoid a U0->U1 dependency), FastAPI
dependencies for injecting/guarding context, and bcrypt password helpers.

Multi-tenancy rule (BR-U0-3): ``store_id`` always comes from the verified
token, never from client-supplied request data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends, Header
from passlib.context import CryptContext

from app.common.exceptions import AuthError, ForbiddenError

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- password helpers (used by U1) ---------------------------------------
def hash_password(raw: str) -> str:
    return _pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd_context.verify(raw, hashed)


# --- tenant context -------------------------------------------------------
@dataclass(frozen=True)
class StoreContext:
    """Authenticated request context. ``store_id`` is the isolation key."""

    store_id: int
    role: str  # "admin" | "table"
    subject: str
    table_id: int | None = None


class TokenVerifier(Protocol):
    """Implemented by U1 Auth; verifies a bearer token into a StoreContext."""

    def verify(self, token: str) -> StoreContext: ...


_verifier: TokenVerifier | None = None


def register_token_verifier(verifier: TokenVerifier) -> None:
    """Called by U1 at app startup to plug in real token verification."""
    global _verifier
    _verifier = verifier


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("missing bearer token")
    return authorization[7:].strip()


def get_current_store_context(
    authorization: str | None = Header(default=None),
) -> StoreContext:
    """FastAPI dependency: resolve the authenticated StoreContext (BR-U0-5)."""
    if _verifier is None:
        # Misconfiguration: Auth unit did not register a verifier (BR-U0-7).
        logger.error("No TokenVerifier registered; authentication unavailable.")
        raise AuthError("authentication not configured")
    token = _extract_bearer(authorization)
    return _verifier.verify(token)


def require_admin(
    ctx: StoreContext = Depends(get_current_store_context),
) -> StoreContext:
    if ctx.role != "admin":
        raise ForbiddenError("admin role required")
    return ctx


def require_table(
    ctx: StoreContext = Depends(get_current_store_context),
) -> StoreContext:
    if ctx.role != "table":
        raise ForbiddenError("table role required")
    return ctx


def verify_token(token: str) -> StoreContext:
    """Verify a raw token into a StoreContext (Contract E, additive).

    Mirrors ``get_current_store_context`` but takes the token directly instead of
    parsing an Authorization header. Used by SSE endpoints (U4), where the browser
    ``EventSource`` cannot set headers and passes the token via query string.
    """
    if _verifier is None:
        # Misconfiguration: Auth unit did not register a verifier (BR-U0-7).
        logger.error("No TokenVerifier registered; authentication unavailable.")
        raise AuthError("authentication not configured")
    return _verifier.verify(token)
