"""U4 Session API schemas (pydantic v2).

Response/request models for the admin dashboard (US-A5), session close
(US-A6) and order history (US-A7). ``from_attributes`` enables ORM->schema
mapping for history rows/lines.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RecentOrder(BaseModel):
    order_no: str
    order_status: str
    order_amount: int
    ordered_at: datetime


class DashboardCard(BaseModel):
    table_id: int
    table_number: str | None
    session_id: int
    total_amount: int
    started_at: datetime
    recent_orders: list[RecentOrder]


class CloseSessionRequest(BaseModel):
    table_id: int


class ClosedSessionSummary(BaseModel):
    table_id: int
    session_id: int
    total_amount: int
    closed_at: datetime
    order_count: int


class HistoryOrderLineOut(BaseModel):
    model_config = {"from_attributes": True}

    menu_name: str
    quantity: int
    unit_price: int


class HistoryOrderOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    session_id: int
    table_id: int
    order_no: str
    order_status: str
    order_amount: int
    ordered_at: datetime
    closed_at: datetime | None
    lines: list[HistoryOrderLineOut]
