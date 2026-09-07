"""U1 AuthService — orchestrates login, throttling, token issue, table setup.

Repositories flush; the service commits writes (U0 seed convention). Uniform
failure messages avoid store/account enumeration (BR-U1-8). ``store_id`` for
authenticated operations always comes from ``StoreContext`` (BR-U1-7).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.exceptions import AuthError, NotFoundError, ValidationError
from app.common.security import StoreContext, hash_password, verify_password

from app.auth import tokens
from app.auth.attempts import tracker
from app.auth.repository import AdminUserRepository, StoreResolver, TableRepository
from app.auth.schemas import StoreInfo, TableResponse, TokenResponse

_INVALID_CREDENTIALS = "invalid credentials"
_TOO_MANY_ATTEMPTS = "too many attempts; try again later"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.stores = StoreResolver(db)
        self.admins = AdminUserRepository(db)
        self.tables = TableRepository(db)

    # --- admin login (US-A1) ---------------------------------------------
    def admin_login(self, store_code: str, username: str, password: str) -> TokenResponse:
        store = self.stores.get_by_code(store_code)
        # Do not reveal whether the store exists (BR-U1-8). Still enforce the
        # lock check on a resolved store to prevent bypass.
        if store is not None and tracker.is_locked(store.id, username):
            raise AuthError(_TOO_MANY_ATTEMPTS)

        user = self.admins.get_by_username(store.id, username) if store else None
        if user is None or not verify_password(password, user.password_hash):
            if store is not None:
                tracker.record_failure(store.id, username)
            raise AuthError(_INVALID_CREDENTIALS)

        tracker.reset(store.id, username)
        token, expires_in = tokens.issue_admin(store.id, username)
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            store=StoreInfo(code=store.code, name=store.name),
            subject=username,
        )

    # --- table login (US-C1) — no throttling (Q4=A) ----------------------
    def table_login(
        self, store_code: str, table_number: str, password: str
    ) -> TokenResponse:
        store = self.stores.get_by_code(store_code)
        table = self.tables.get_by_number(store.id, table_number) if store else None
        if table is None or not verify_password(password, table.password_hash):
            raise AuthError(_INVALID_CREDENTIALS)

        token, expires_in = tokens.issue_table(store.id, table.id)
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            store=StoreInfo(code=store.code, name=store.name),
            table_id=table.id,
        )

    # --- table setup (US-A4, require_admin) ------------------------------
    def list_tables(self, ctx: StoreContext) -> list[TableResponse]:
        rows = self.tables.list(ctx.store_id, limit=200)
        return [TableResponse(id=t.id, table_number=t.table_number) for t in rows]

    def create_table(
        self, ctx: StoreContext, table_number: str, password: str
    ) -> TableResponse:
        if self.tables.get_by_number(ctx.store_id, table_number) is not None:
            raise ValidationError(f"table number '{table_number}' already exists")
        table = self.tables.create(
            ctx.store_id,
            table_number=table_number,
            password_hash=hash_password(password),
        )
        self.db.commit()
        return TableResponse(id=table.id, table_number=table.table_number)

    def update_table(
        self,
        ctx: StoreContext,
        table_id: int,
        table_number: str | None = None,
        password: str | None = None,
    ) -> TableResponse:
        table = self.tables.get(ctx.store_id, table_id)
        if table is None:
            raise NotFoundError("table not found")

        if table_number is not None and table_number != table.table_number:
            existing = self.tables.get_by_number(ctx.store_id, table_number)
            if existing is not None and existing.id != table_id:
                raise ValidationError(f"table number '{table_number}' already exists")
            table.table_number = table_number

        if password is not None:
            table.password_hash = hash_password(password)

        self.db.flush()
        self.db.commit()
        return TableResponse(id=table.id, table_number=table.table_number)
