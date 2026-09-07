"""U1 TokenService + JwtTokenVerifier (Contract E).

JWT (HS256) encode/decode. Admin tokens expire in 16h, table tokens in 720h
(config). ``JwtTokenVerifier`` implements U0's ``TokenVerifier`` protocol and is
registered at app startup via ``register_token_verifier`` (BR-U1-9/10/10a).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.common.config import settings
from app.common.exceptions import AuthError
from app.common.security import StoreContext


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(claims: dict) -> str:
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def issue_admin(store_id: int, username: str) -> tuple[str, int]:
    """Admin token: role=admin, sub=username. Returns (token, expires_in_seconds)."""
    expires_in = settings.admin_token_expire_hours * 3600
    iat = _now()
    claims = {
        "sub": username,
        "store_id": store_id,
        "role": "admin",
        "iat": iat,
        "exp": iat + timedelta(seconds=expires_in),
    }
    return _encode(claims), expires_in


def issue_table(store_id: int, table_id: int) -> tuple[str, int]:
    """Table token: role=table, sub='table:{id}'. Returns (token, expires_in_seconds)."""
    expires_in = settings.table_token_expire_hours * 3600
    iat = _now()
    claims = {
        "sub": f"table:{table_id}",
        "store_id": store_id,
        "role": "table",
        "table_id": table_id,
        "iat": iat,
        "exp": iat + timedelta(seconds=expires_in),
    }
    return _encode(claims), expires_in


class JwtTokenVerifier:
    """Contract E implementation of U0's ``TokenVerifier`` protocol."""

    def verify(self, token: str) -> StoreContext:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except JWTError as exc:  # signature/expiry failures (BR-U1-10a)
            raise AuthError("invalid or expired token") from exc
        try:
            return StoreContext(
                store_id=payload["store_id"],
                role=payload["role"],
                subject=payload["sub"],
                table_id=payload.get("table_id"),
            )
        except KeyError as exc:
            raise AuthError("invalid token claims") from exc
