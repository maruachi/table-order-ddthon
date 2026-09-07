"""U3 order router tests via FastAPI TestClient with dependency overrides."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.common.database import Base, get_db
from app.common.models import Store  # noqa: F401 register
from app.common.security import (
    StoreContext,
    get_current_store_context,
    require_admin,
    require_table,
)
from app.main import create_app
from app.order import models as _order_models  # noqa: F401 register
from app.order.gateways import MenuItemInfo, StubMenuLookup, StubSessionGateway
from app.order.router import get_menu_lookup, get_session_gateway

CATALOG = {1: MenuItemInfo(id=1, name="아메리카노", price=4000, available=True)}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # share one in-memory DB across TestClient threads
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    seed = Session()
    seed.add(Store(id=1, code="s1", name="S1"))
    seed.commit()
    seed.close()

    session_gateway = StubSessionGateway()

    def _override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_menu_lookup] = lambda: StubMenuLookup(CATALOG)
    app.dependency_overrides[get_session_gateway] = lambda: session_gateway
    app.dependency_overrides[require_table] = lambda: StoreContext(
        store_id=1, role="table", subject="t7", table_id=7
    )
    app.dependency_overrides[require_admin] = lambda: StoreContext(
        store_id=1, role="admin", subject="owner"
    )
    app.dependency_overrides[get_current_store_context] = lambda: StoreContext(
        store_id=1, role="admin", subject="owner"
    )
    with TestClient(app) as c:
        yield c


def test_create_and_list_and_status_flow(client):
    # create
    r = client.post("/orders", json={"items": [{"menu_id": 1, "qty": 2}]})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total"] == 8000
    assert body["order_no"] == 1
    order_id = body["id"]
    assert len(body["items"]) == 1

    # current list
    r = client.get("/orders/current")
    assert r.status_code == 200
    assert r.json()["total"] == 1

    # status change
    r = client.patch(f"/orders/{order_id}/status", json={"status": "preparing"})
    assert r.status_code == 200
    assert r.json()["status"] == "preparing"

    # detail
    r = client.get(f"/orders/{order_id}")
    assert r.status_code == 200

    # dashboard
    r = client.get("/orders/dashboard")
    assert r.status_code == 200
    assert r.json()[0]["order_count"] == 1


def test_empty_order_rejected(client):
    r = client.post("/orders", json={"items": []})
    assert r.status_code == 422  # pydantic min_length


def test_delete_recomputes_total(client):
    r1 = client.post("/orders", json={"items": [{"menu_id": 1, "qty": 1}]})
    r2 = client.post("/orders", json={"items": [{"menu_id": 1, "qty": 1}]})
    id1 = r1.json()["id"]
    r = client.delete(f"/orders/{id1}")
    assert r.status_code == 200
    assert r.json()["total"] == 4000  # one order remaining
    # deleted order not found
    assert client.get(f"/orders/{id1}").status_code == 404


def test_invalid_status_rejected(client):
    r = client.post("/orders", json={"items": [{"menu_id": 1, "qty": 1}]})
    oid = r.json()["id"]
    r = client.patch(f"/orders/{oid}/status", json={"status": "bogus"})
    assert r.status_code == 422  # enum validation
