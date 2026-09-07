"""Store-scoped base repository (U0) — enforces multi-tenancy (NFR-3).

Every read/write requires an explicit ``store_id`` and always filters by it
(BR-U0-2). Domain repositories subclass this and get isolation for free.
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model
        if not hasattr(model, "store_id"):
            raise TypeError(
                f"{model.__name__} has no store_id; not usable with BaseRepository"
            )

    def _scoped(self, store_id: int):
        return select(self.model).where(self.model.store_id == store_id)

    def get(self, store_id: int, id_: int) -> ModelT | None:
        stmt = self._scoped(store_id).where(self.model.id == id_)
        return self.db.scalars(stmt).first()

    def list(
        self,
        store_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> Sequence[ModelT]:
        stmt = self._scoped(store_id)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.offset(offset).limit(limit)
        return self.db.scalars(stmt).all()

    def count(self, store_id: int, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.store_id == store_id
        )
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return int(self.db.scalar(stmt) or 0)

    def create(self, store_id: int, **fields: Any) -> ModelT:
        obj = self.model(store_id=store_id, **fields)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, store_id: int, id_: int, **fields: Any) -> ModelT | None:
        obj = self.get(store_id, id_)
        if obj is None:
            return None
        for key, value in fields.items():
            setattr(obj, key, value)
        self.db.flush()
        return obj

    def delete(self, store_id: int, id_: int) -> bool:
        obj = self.get(store_id, id_)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True
