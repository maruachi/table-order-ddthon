"""U0 common-layer tests: tenant isolation, context guards, exceptions."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.database import Base
from app.common.exceptions import AuthError, ForbiddenError
from app.common.models import Store, Table
from app.common.repository import BaseRepository
from app.common.security import (
    StoreContext,
    hash_password,
    require_admin,
    verify_password,
)


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
    return a, b


def test_base_repository_enforces_store_isolation(db, two_stores):
    a, b = two_stores
    repo = BaseRepository(db, Table)
    t_a = repo.create(a.id, table_number="1", password_hash="x")
    repo.create(b.id, table_number="1", password_hash="x")
    db.flush()

    # store A only sees its own table
    assert {t.id for t in repo.list(a.id)} == {t_a.id}
    # cross-tenant get returns None (fail-closed, BR-U0-4)
    assert repo.get(b.id, t_a.id) is None
    assert repo.count(a.id) == 1


def test_base_repository_rejects_model_without_store_id(db):
    with pytest.raises(TypeError):
        BaseRepository(db, Store)  # Store has no store_id column


def test_password_hash_roundtrip():
    h = hash_password("secret")
    assert h != "secret"
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)


def test_require_admin_guard():
    admin = StoreContext(store_id=1, role="admin", subject="owner")
    table = StoreContext(store_id=1, role="table", subject="t1", table_id=1)
    assert require_admin(admin) is admin
    with pytest.raises(ForbiddenError):
        require_admin(table)


def test_get_context_without_verifier_raises(monkeypatch):
    import app.common.security as sec

    monkeypatch.setattr(sec, "_verifier", None)
    with pytest.raises(AuthError):
        sec.get_current_store_context(authorization="Bearer abc")
