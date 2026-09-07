"""Seed script (U0): create sample stores and tables for local dev.

Run from the backend/ directory:  python -m seeds.seed
Idempotent: skips stores/tables that already exist.
"""
from __future__ import annotations

from app.common.database import SessionLocal, init_db
from app.common.models import Store, Table
from app.common.security import hash_password
from app.menu.models import Category, Menu

SAMPLE_STORES = [
    {"code": "demo-cafe", "name": "데모 카페", "tables": 6, "table_pw": "1234"},
    {"code": "demo-bistro", "name": "데모 비스트로", "tables": 4, "table_pw": "1234"},
]

# U2: sample menu per store (category -> list of (name, price, available)).
SAMPLE_MENU = {
    "커피": [("아메리카노", 4000, True), ("카페라떼", 4500, True), ("콜드브루", 5000, False)],
    "디저트": [("치즈케이크", 6500, True), ("초코쿠키", 3000, True)],
}


def _seed_menu(db, store_id: int) -> None:
    """Idempotent: add sample categories/menus for a store if absent (U2)."""
    for cat_order, (cat_name, items) in enumerate(SAMPLE_MENU.items()):
        category = (
            db.query(Category)
            .filter(Category.store_id == store_id, Category.name == cat_name)
            .first()
        )
        if category is None:
            category = Category(
                store_id=store_id, name=cat_name, display_order=cat_order
            )
            db.add(category)
            db.flush()
        for menu_order, (name, price, available) in enumerate(items):
            exists = (
                db.query(Menu)
                .filter(
                    Menu.store_id == store_id,
                    Menu.category_id == category.id,
                    Menu.name == name,
                )
                .first()
            )
            if exists is None:
                db.add(
                    Menu(
                        store_id=store_id,
                        category_id=category.id,
                        name=name,
                        price=price,
                        available=available,
                        display_order=menu_order,
                    )
                )


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        for s in SAMPLE_STORES:
            store = db.query(Store).filter(Store.code == s["code"]).first()
            if store is None:
                store = Store(code=s["code"], name=s["name"])
                db.add(store)
                db.flush()
                print(f"created store {store.code} (id={store.id})")
            for n in range(1, s["tables"] + 1):
                number = str(n)
                exists = (
                    db.query(Table)
                    .filter(Table.store_id == store.id, Table.table_number == number)
                    .first()
                )
                if exists is None:
                    db.add(
                        Table(
                            store_id=store.id,
                            table_number=number,
                            password_hash=hash_password(s["table_pw"]),
                        )
                    )
            _seed_menu(db, store.id)
            db.commit()
        print("seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
