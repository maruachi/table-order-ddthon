"""Application configuration (U0 Platform/Common).

Central settings loaded from environment (with sensible local-dev defaults).
Shared by all units.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TO_", extra="ignore")

    # Database
    database_url: str = "sqlite:///./table_order.db"

    # Auth / tokens (used by U1; defined here as shared config)
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    admin_token_expire_hours: int = 16  # US-A1: 16h admin session
    table_token_expire_hours: int = 24 * 30  # long-lived table token

    # CORS: customer & admin SPA dev origins
    cors_origins: list[str] = [
        "http://localhost:5173",  # frontend-customer (Vite default)
        "http://localhost:5174",  # frontend-admin
    ]

    # Auth policy (NFR-2)
    max_login_attempts: int = 5
    lockout_minutes: int = 15  # U1: lock duration after too many attempts (TO_LOCKOUT_MINUTES, Q1=A)


settings = Settings()
