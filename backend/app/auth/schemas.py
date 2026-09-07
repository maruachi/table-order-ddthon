"""U1 Auth request/response schemas (pydantic v2).

Table responses never expose ``password_hash`` (BR-U1-12). Non-blank
validation for credentials/table fields (BR-U1-15).
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _non_blank(value: str) -> str:
    if value is None or not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


# --- login requests -------------------------------------------------------
class AdminLoginRequest(BaseModel):
    store_code: str
    username: str
    password: str

    _v = field_validator("store_code", "username", "password")(_non_blank)


class TableLoginRequest(BaseModel):
    store_code: str
    table_number: str
    password: str

    _v = field_validator("store_code", "table_number", "password")(_non_blank)


# --- token response -------------------------------------------------------
class StoreInfo(BaseModel):
    code: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    store: StoreInfo
    subject: str | None = None
    table_id: int | None = None


# --- table setup (US-A4) --------------------------------------------------
class TableCreateRequest(BaseModel):
    table_number: str
    password: str

    _v = field_validator("table_number", "password")(_non_blank)


class TableUpdateRequest(BaseModel):
    """Both fields optional; only provided fields are updated."""

    table_number: str | None = Field(default=None)
    password: str | None = Field(default=None)

    @field_validator("table_number", "password")
    @classmethod
    def _optional_non_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class TableResponse(BaseModel):
    """Table view — never includes password_hash (BR-U1-12)."""

    id: int
    table_number: str
