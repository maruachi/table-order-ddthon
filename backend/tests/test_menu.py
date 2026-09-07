"""U2 Menu service tests: isolation, CRUD, soft-delete, availability, reorder,
Contract A. Exercises the service layer against an in-memory SQLite DB."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.database import Base
from app.common.exceptions import NotFoundError, ValidationError
from app.common.models import Store
from app.menu import models as _menu_models  # noqa: F401  (register tables)
from app.menu.service import MenuService


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def two_stores(db):
    a = Store(code="a", name="A")
    b = Store(code="b", name="B")
    db.add_all([a, b])
    db.flush()
    return a.id, b.id


def _seed_category_and_menu(svc: MenuService, store_id: int, name="아메리카노", price=4000):
    cat = svc.create_category(store_id, "커피")
    menu = svc.create_menu(
        store_id,
        category_id=cat.id,
        name=name,
        price=price,
        description=None,
        image_url=None,
    )
    return cat, menu


def test_category_crud_and_unique_name(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    cat = svc.create_category(store_id, "커피")
    assert cat.display_order == 1
    with pytest.raises(ValidationError):
        svc.create_category(store_id, "커피")  # duplicate name
    svc.update_category(store_id, cat.id, "음료")
    assert svc.list_categories(store_id)[0].name == "음료"


def test_menu_crud_and_category_validation(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    _, menu = _seed_category_and_menu(svc, store_id)
    assert menu.price == 4000
    with pytest.raises(ValidationError):
        svc.create_menu(
            store_id, category_id=9999, name="x", price=1, description=None, image_url=None
        )


def test_store_isolation(db, two_stores):
    a, b = two_stores
    svc = MenuService(db)
    _seed_category_and_menu(svc, a)
    # store B sees nothing that belongs to A
    assert svc.list_categories(b) == []
    assert svc.list_menus_admin(b) == []


def test_soft_delete_hides_menu_but_keeps_availability_semantics(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    cat, menu = _seed_category_and_menu(svc, store_id)
    svc.delete_menu(store_id, menu.id)
    # excluded from admin list, customer view, and Contract A
    assert svc.list_menus_admin(store_id) == []
    groups = svc.list_menus_for_customer(store_id)
    assert groups[0]["menus"] == []
    assert svc.get_menu_items(store_id, [menu.id]) == []
    # deleting again -> not found
    with pytest.raises(NotFoundError):
        svc.delete_menu(store_id, menu.id)


def test_sold_out_menu_is_shown_but_flagged(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    cat, menu = _seed_category_and_menu(svc, store_id)
    svc.set_menu_availability(store_id, menu.id, False)
    groups = svc.list_menus_for_customer(store_id)
    assert groups[0]["menus"][0].available is False  # still present
    items = svc.get_menu_items(store_id, [menu.id])
    assert items == [{"id": menu.id, "name": "아메리카노", "price": 4000, "available": False}]


def test_delete_category_requires_no_active_menus(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    cat, menu = _seed_category_and_menu(svc, store_id)
    with pytest.raises(ValidationError):
        svc.delete_category(store_id, cat.id)
    svc.delete_menu(store_id, menu.id)
    svc.delete_category(store_id, cat.id)  # now allowed
    assert svc.list_categories(store_id) == []


def test_reorder_requires_full_set(db, two_stores):
    store_id, _ = two_stores
    svc = MenuService(db)
    c1 = svc.create_category(store_id, "커피")
    c2 = svc.create_category(store_id, "디저트")
    svc.reorder_categories(store_id, [c2.id, c1.id])
    ordered = svc.list_categories(store_id)
    assert [c.id for c in ordered] == [c2.id, c1.id]
    with pytest.raises(ValidationError):
        svc.reorder_categories(store_id, [c1.id])  # incomplete set


def test_contract_a_omits_unknown_and_cross_tenant(db, two_stores):
    a, b = two_stores
    svc = MenuService(db)
    _, menu_a = _seed_category_and_menu(svc, a)
    # unknown id omitted; cross-tenant id omitted (fail-closed)
    result = svc.get_menu_items(a, [menu_a.id, 999999])
    assert [r["id"] for r in result] == [menu_a.id]
    assert svc.get_menu_items(b, [menu_a.id]) == []
