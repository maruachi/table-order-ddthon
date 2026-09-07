"""U1 Auth repositories.

``AdminUserRepository`` and ``TableRepository`` inherit U0 ``BaseRepository``
so every query is store-scoped automatically (NFR-3, BR-U1-7). ``StoreResolver``
resolves a login ``store_code`` -> ``Store`` (pre-auth lookup; not store-scoped).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.models import Store, Table
from app.common.repository import BaseRepository

from app.auth.models import AdminUser


class AdminUserRepository(BaseRepository[AdminUser]):
    def __init__(self, db: Session):
        super().__init__(db, AdminUser)

    def get_by_username(self, store_id: int, username: str) -> AdminUser | None:
        stmt = self._scoped(store_id).where(self.model.username == username)
        return self.db.scalars(stmt).first()


class TableRepository(BaseRepository[Table]):
    def __init__(self, db: Session):
        super().__init__(db, Table)

    def get_by_number(self, store_id: int, table_number: str) -> Table | None:
        stmt = self._scoped(store_id).where(self.model.table_number == table_number)
        return self.db.scalars(stmt).first()


class StoreResolver:
    """Resolves a store by its business code at login (pre-auth, not scoped)."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> Store | None:
        return self.db.scalars(select(Store).where(Store.code == code)).first()
