"""U1 Auth API layer.

Public login endpoints + admin-protected table setup endpoints. Typed
``AppError``s bubble up to U0's central exception handlers (BR-U0-10).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.common.security import StoreContext, require_admin

from app.auth.schemas import (
    AdminLoginRequest,
    TableCreateRequest,
    TableLoginRequest,
    TableResponse,
    TableUpdateRequest,
    TokenResponse,
)
from app.auth.service import AuthService

router = APIRouter(prefix="/api", tags=["auth"])


# --- public login ---------------------------------------------------------
@router.post("/auth/admin/login", response_model=TokenResponse)
def admin_login(body: AdminLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).admin_login(body.store_code, body.username, body.password)


@router.post("/auth/table/login", response_model=TokenResponse)
def table_login(body: TableLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).table_login(body.store_code, body.table_number, body.password)


# --- admin table setup (require_admin) ------------------------------------
@router.get("/admin/tables", response_model=list[TableResponse])
def list_tables(
    ctx: StoreContext = Depends(require_admin), db: Session = Depends(get_db)
) -> list[TableResponse]:
    return AuthService(db).list_tables(ctx)


@router.post("/admin/tables", response_model=TableResponse, status_code=201)
def create_table(
    body: TableCreateRequest,
    ctx: StoreContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TableResponse:
    return AuthService(db).create_table(ctx, body.table_number, body.password)


@router.put("/admin/tables/{table_id}", response_model=TableResponse)
def update_table(
    table_id: int,
    body: TableUpdateRequest,
    ctx: StoreContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TableResponse:
    return AuthService(db).update_table(
        ctx, table_id, table_number=body.table_number, password=body.password
    )
