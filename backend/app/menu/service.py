"""U2 Menu service (business logic, 3-layer middle).

Enforces business rules (business-rules.md), raises typed U0 AppErrors on
violations, and exposes Contract A (``get_menu_items``) for U3 Order.

store_id is always supplied by the caller from StoreContext (never client
input, BR-U0-3 / BR-U2-0). U2 publishes no realtime events.
"""
from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationError
from app.menu.models import Category, Menu
from app.menu.repository import CategoryRepository, MenuRepository


class MenuService:
    def __init__(self, db: Session):
        self.db = db
        self.categories = CategoryRepository(db)
        self.menus = MenuRepository(db)

    # --- categories -----------------------------------------------------

    def list_categories(self, store_id: int) -> Sequence[Category]:
        return self.categories.list_ordered(store_id)

    def create_category(self, store_id: int, name: str) -> Category:
        if self.categories.get_by_name(store_id, name) is not None:
            raise ValidationError(f"category name already exists: {name}")
        order = self.categories.max_display_order(store_id) + 1
        cat = self.categories.create(store_id, name=name, display_order=order)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def update_category(self, store_id: int, category_id: int, name: str) -> Category:
        cat = self.categories.get(store_id, category_id)
        if cat is None:
            raise NotFoundError("category not found")
        existing = self.categories.get_by_name(store_id, name)
        if existing is not None and existing.id != category_id:
            raise ValidationError(f"category name already exists: {name}")
        cat.name = name
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def delete_category(self, store_id: int, category_id: int) -> None:
        cat = self.categories.get(store_id, category_id)
        if cat is None:
            raise NotFoundError("category not found")
        # Only deletable when it holds no active (non-deleted) menus (BR-U2-13).
        if self.menus.has_active_menus(store_id, category_id):
            raise ValidationError("category still has active menus")
        self.categories.delete(store_id, category_id)
        self.db.commit()

    def reorder_categories(self, store_id: int, ordered_ids: list[int]) -> None:
        current = list(self.categories.list_ordered(store_id))
        self._assert_full_set(ordered_ids, [c.id for c in current], "category")
        by_id = {c.id: c for c in current}
        for position, cid in enumerate(ordered_ids):
            by_id[cid].display_order = position
        self.db.commit()

    # --- menus (admin) --------------------------------------------------

    def list_menus_admin(self, store_id: int) -> Sequence[Menu]:
        return self.menus.list_active(store_id)

    def create_menu(
        self,
        store_id: int,
        *,
        category_id: int,
        name: str,
        price: int,
        description: str | None,
        image_url: str | None,
    ) -> Menu:
        self._require_category(store_id, category_id)
        order = self.menus.max_display_order(store_id, category_id) + 1
        menu = self.menus.create(
            store_id,
            category_id=category_id,
            name=name,
            price=price,
            description=description,
            image_url=image_url,
            display_order=order,
        )
        self.db.commit()
        self.db.refresh(menu)
        return menu

    def update_menu(
        self,
        store_id: int,
        menu_id: int,
        *,
        category_id: int,
        name: str,
        price: int,
        description: str | None,
        image_url: str | None,
    ) -> Menu:
        menu = self.menus.get_active(store_id, menu_id)
        if menu is None:
            raise NotFoundError("menu not found")
        self._require_category(store_id, category_id)
        moved = menu.category_id != category_id
        menu.category_id = category_id
        menu.name = name
        menu.price = price
        menu.description = description
        menu.image_url = image_url
        if moved:
            menu.display_order = self.menus.max_display_order(store_id, category_id) + 1
        self.db.commit()
        self.db.refresh(menu)
        return menu

    def delete_menu(self, store_id: int, menu_id: int) -> None:
        menu = self.menus.get_active(store_id, menu_id)
        if menu is None:
            raise NotFoundError("menu not found")
        menu.is_deleted = True  # soft delete (Q3:B / BR-U2-11)
        self.db.commit()

    def set_menu_availability(self, store_id: int, menu_id: int, available: bool) -> Menu:
        menu = self.menus.get_active(store_id, menu_id)
        if menu is None:
            raise NotFoundError("menu not found")
        menu.available = available
        self.db.commit()
        self.db.refresh(menu)
        return menu

    def reorder_menus(self, store_id: int, category_id: int, ordered_ids: list[int]) -> None:
        self._require_category(store_id, category_id)
        current = list(self.menus.list_active_by_category(store_id, category_id))
        self._assert_full_set(ordered_ids, [m.id for m in current], "menu")
        by_id = {m.id: m for m in current}
        for position, mid in enumerate(ordered_ids):
            by_id[mid].display_order = position
        self.db.commit()

    # --- customer read --------------------------------------------------

    def list_menus_for_customer(self, store_id: int) -> list[dict]:
        """Grouped-by-category response (Q9:A). Sold-out items are included
        (available=false); soft-deleted items are excluded."""
        categories = self.categories.list_ordered(store_id)
        menus = self.menus.list_active(store_id)
        grouped: dict[int, list[Menu]] = {}
        for m in menus:
            grouped.setdefault(m.category_id, []).append(m)
        result: list[dict] = []
        for cat in categories:
            items = sorted(
                grouped.get(cat.id, []), key=lambda m: (m.display_order, m.id)
            )
            result.append(
                {
                    "id": cat.id,
                    "name": cat.name,
                    "display_order": cat.display_order,
                    "menus": items,
                }
            )
        return result

    # --- Contract A (consumed by U3 Order) ------------------------------

    def get_menu_items(self, store_id: int, menu_ids: Sequence[int]) -> list[dict]:
        """Contract A: return {id, name, price, available} for the requested,
        store-scoped, non-deleted menus. Deleted/nonexistent ids are omitted;
        sold-out items are returned with available=false. Order-eligibility is
        U3's judgment; server price is the trust source (BR-U2-15/16)."""
        menus = self.menus.list_active_by_ids(store_id, menu_ids)
        return [
            {
                "id": m.id,
                "name": m.name,
                "price": m.price,
                "available": m.available,
            }
            for m in menus
        ]

    # --- helpers --------------------------------------------------------

    def _require_category(self, store_id: int, category_id: int) -> Category:
        cat = self.categories.get(store_id, category_id)
        if cat is None:
            raise ValidationError(f"category_id does not exist: {category_id}")
        return cat

    @staticmethod
    def _assert_full_set(ordered_ids: list[int], current_ids: list[int], label: str) -> None:
        if sorted(ordered_ids) != sorted(current_ids):
            raise ValidationError(
                f"reorder {label} ids must exactly match the current active set"
            )
