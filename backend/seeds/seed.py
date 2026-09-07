"""Seed script (U0): create sample stores and tables for local dev.

Run from the backend/ directory:  python -m seeds.seed
Idempotent: skips stores/tables that already exist.
"""
from __future__ import annotations

from app.auth.models import AdminUser
from app.common.database import SessionLocal, init_db
from app.common.models import Store, Table
from app.common.security import hash_password

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
            db.commit()
        print("seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
