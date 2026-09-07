"""U2 Menu Pydantic schemas (request/response boundary).

Validation lives here (BR-U2-1~5, Q6:B/Q7:B): ``price`` is a non-negative
integer, ``image_url`` (optional) must be a valid http(s) URL, ``name`` is
required, ``description`` optional.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# --- Category ------------------------------------------------------------


class CategoryInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_order: int


# --- Menu ----------------------------------------------------------------


class MenuInput(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)  # KRW integer, no upper bound (Q6:B)
    description: str | None = None
    image_url: HttpUrl | None = None  # http(s) validated (Q7:B)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v


class MenuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    price: int
    description: str | None
    image_url: str | None
    display_order: int
    available: bool


class CategoryWithMenus(BaseModel):
    """Customer grouped response element (Q9:A)."""

    id: int
    name: str
    display_order: int
    menus: list[MenuOut]


# --- Operations ----------------------------------------------------------


class ReorderInput(BaseModel):
    """Full-set reorder: ordered_ids must equal the current active set (BR-U2-6/7)."""

    ordered_ids: list[int] = Field(min_length=0)


class AvailabilityInput(BaseModel):
    available: bool
