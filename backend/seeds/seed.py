"""Seed script (U0): create sample stores and tables for local dev.

Run from the backend/ directory:  python -m seeds.seed
Idempotent: skips stores/tables that already exist.
"""
from __future__ import annotations

from app.auth.models import AdminUser
from app.common.database import SessionLocal, init_db
from app.common.models import Store, Table
from app.common.security import hash_password
from app.menu.models import Category, Menu

SAMPLE_STORES = [
    {
        "code": "demo-cafe",
        "name": "데모 카페",
        "tables": 6,
        "table_pw": "1234",
        "admin_user": "admin",
        "admin_pw": "admin1234",
    },
    {
        "code": "demo-bistro",
        "name": "데모 비스트로",
        "tables": 4,
        "table_pw": "1234",
        "admin_user": "admin",
        "admin_pw": "admin1234",
    },
]

# U2: sample menu per store (category -> list of (name, price, available, image_url)).
# image_url must be a valid http(s) URL (Menu.image_url is HttpUrl-validated);
# these are stable Unsplash photo URLs matching each item for local dev preview.
SAMPLE_MENU = {
    "커피": [
        ("아메리카노", 4000, True, "https://images.unsplash.com/photo-1521302080334-4bebac2763a6?w=600&q=80"),
        ("카페라떼", 4500, True, "https://images.unsplash.com/photo-1561047029-3000c68339ca?w=600&q=80"),
        ("콜드브루", 5000, False, "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=600&q=80"),
    ],
    "디저트": [
        ("치즈케이크", 6500, True, "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&q=80"),
        ("초코쿠키", 3000, True, "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=600&q=80"),
    ],
}


def _seed_menu(db, store_id: int) -> None:
    """Idempotent: add sample categories/menus for a store if absent (U2).

    Backfills image_url on existing rows that were seeded before images were added.
    """
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
        for menu_order, (name, price, available, image_url) in enumerate(items):
            existing = (
                db.query(Menu)
                .filter(
                    Menu.store_id == store_id,
                    Menu.category_id == category.id,
                    Menu.name == name,
                )
                .first()
            )
            if existing is None:
                db.add(
                    Menu(
                        store_id=store_id,
                        category_id=category.id,
                        name=name,
                        price=price,
                        available=available,
                        image_url=image_url,
                        display_order=menu_order,
                    )
                )
            elif existing.image_url is None:
                existing.image_url = image_url


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
            # Admin account per store (seed-only provisioning, Q1=A).
            admin_exists = (
                db.query(AdminUser)
                .filter(
                    AdminUser.store_id == store.id,
                    AdminUser.username == s["admin_user"],
                )
                .first()
            )
            if admin_exists is None:
                db.add(
                    AdminUser(
                        store_id=store.id,
                        username=s["admin_user"],
                        password_hash=hash_password(s["admin_pw"]),
                    )
                )
                print(f"created admin {s['admin_user']} for store {store.code}")
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
