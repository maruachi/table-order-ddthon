"""Order API schemas (U3)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    pending = "pending"
    preparing = "preparing"
    done = "done"


class OrderItemIn(BaseModel):
    menu_id: int
    qty: int = Field(gt=0, description="수량 (1 이상)")


class OrderInput(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, description="주문 항목 (최소 1개)")


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    menu_id: int
    menu_name: str
    unit_price: int
    qty: int
    line_total: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: int
    session_id: int
    table_id: int
    status: OrderStatus
    total: int
    created_at: datetime


class OrderDetailOut(OrderOut):
    items: list[OrderItemOut]


class StatusUpdateIn(BaseModel):
    status: OrderStatus


class TableTotals(BaseModel):
    table_id: int
    total: int


class TableCard(BaseModel):
    table_id: int
    total: int
    order_count: int
    latest_orders: list[OrderOut]
