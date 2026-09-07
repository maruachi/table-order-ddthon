"""U2 Menu repositories (store-scoped via U0 BaseRepository, NFR-3).

Every query is filtered by ``store_id`` for free through BaseRepository.
Soft-deleted menus (``is_deleted=True``) are excluded from all reads here.
"""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.repository import BaseRepository
from app.menu.models import Category, Menu


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)

    def list_ordered(self, store_id: int) -> Sequence[Category]:
        stmt = (
            self._scoped(store_id)
            .order_by(Category.display_order, Category.id)
        )
        return self.db.scalars(stmt).all()

    def get_by_name(self, store_id: int, name: str) -> Category | None:
        stmt = self._scoped(store_id).where(Category.name == name)
        return self.db.scalars(stmt).first()

    def max_display_order(self, store_id: int) -> int:
        stmt = select(func.max(Category.display_order)).where(
            Category.store_id == store_id
        )
        return int(self.db.scalar(stmt) or 0)


class MenuRepository(BaseRepository[Menu]):
    def __init__(self, db: Session):
        super().__init__(db, Menu)

    def _active(self, store_id: int):
        return self._scoped(store_id).where(Menu.is_deleted.is_(False))

    def get_active(self, store_id: int, id_: int) -> Menu | None:
        stmt = self._active(store_id).where(Menu.id == id_)
        return self.db.scalars(stmt).first()

    def list_active(self, store_id: int) -> Sequence[Menu]:
        stmt = self._active(store_id).order_by(
            Menu.category_id, Menu.display_order, Menu.id
        )
        return self.db.scalars(stmt).all()

    def list_active_by_category(self, store_id: int, category_id: int) -> Sequence[Menu]:
        stmt = (
            self._active(store_id)
            .where(Menu.category_id == category_id)
            .order_by(Menu.display_order, Menu.id)
        )
        return self.db.scalars(stmt).all()

    def list_active_by_ids(self, store_id: int, ids: Sequence[int]) -> Sequence[Menu]:
        if not ids:
            return []
        stmt = self._active(store_id).where(Menu.id.in_(list(ids)))
        return self.db.scalars(stmt).all()

    def has_active_menus(self, store_id: int, category_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(Menu)
            .where(
                Menu.store_id == store_id,
                Menu.category_id == category_id,
                Menu.is_deleted.is_(False),
            )
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def max_display_order(self, store_id: int, category_id: int) -> int:
        stmt = select(func.max(Menu.display_order)).where(
            Menu.store_id == store_id,
            Menu.category_id == category_id,
            Menu.is_deleted.is_(False),
        )
        return int(self.db.scalar(stmt) or 0)
