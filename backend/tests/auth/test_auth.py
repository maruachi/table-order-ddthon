"""U1 Auth tests: admin/table login, throttling, JWT, tenant isolation, setup."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.attempts import LoginAttemptTracker
from app.auth.models import AdminUser
from app.auth.service import AuthService
from app.auth.tokens import JwtTokenVerifier, issue_admin, issue_table
from app.common.config import settings
from app.common.database import Base
from app.common.exceptions import AuthError, NotFoundError, ValidationError
from app.common.models import Store, Table
from app.common.security import StoreContext, hash_password


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
def seeded(db):
    """Two stores; store A has admin 'owner'/'pw' and table '1'/'tablepw'."""
    a = Store(code="a", name="Store A")
    b = Store(code="b", name="Store B")
    db.add_all([a, b])
    db.flush()
    db.add(AdminUser(store_id=a.id, username="owner", password_hash=hash_password("pw")))
    db.add(Table(store_id=a.id, table_number="1", password_hash=hash_password("tablepw")))
    db.add(Table(store_id=b.id, table_number="1", password_hash=hash_password("tablepw")))
    db.commit()
    return a, b


# --- admin login ----------------------------------------------------------
def test_admin_login_success(db, seeded):
    svc = AuthService(db)
    res = svc.admin_login("a", "owner", "pw")
    assert res.token_type == "bearer"
    assert res.subject == "owner"
    assert res.store.code == "a"
    ctx = JwtTokenVerifier().verify(res.access_token)
    assert ctx.role == "admin" and ctx.store_id == seeded[0].id


def test_admin_login_wrong_password_uniform_error(db, seeded):
    svc = AuthService(db)
    with pytest.raises(AuthError):
        svc.admin_login("a", "owner", "nope")


def test_admin_login_unknown_store_same_error(db, seeded):
    svc = AuthService(db)
    with pytest.raises(AuthError):
        svc.admin_login("does-not-exist", "owner", "pw")


# --- throttling -----------------------------------------------------------
def test_lockout_after_threshold_and_auto_unlock(db, seeded):
    from app.auth import service as service_mod

    tracker = LoginAttemptTracker(max_attempts=3, lockout_minutes=15)
    service_mod.tracker = tracker  # inject a fresh tracker for isolation
    svc = AuthService(db)

    for _ in range(3):
        with pytest.raises(AuthError):
            svc.admin_login("a", "owner", "wrong")
    # Now locked — even the correct password is rejected with too-many-attempts.
    with pytest.raises(AuthError):
        svc.admin_login("a", "owner", "pw")
    assert tracker.is_locked(seeded[0].id, "owner")

    # Simulate lock window elapsing -> auto-unlock (BR-U1-6).
    key = (seeded[0].id, "owner")
    tracker._store[key].locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert tracker.is_locked(seeded[0].id, "owner") is False
    # Correct login now succeeds.
    assert svc.admin_login("a", "owner", "pw").subject == "owner"


def test_success_resets_counter(db, seeded):
    from app.auth import service as service_mod

    tracker = LoginAttemptTracker(max_attempts=3, lockout_minutes=15)
    service_mod.tracker = tracker
    svc = AuthService(db)
    with pytest.raises(AuthError):
        svc.admin_login("a", "owner", "wrong")
    svc.admin_login("a", "owner", "pw")  # success resets
    assert tracker._store.get((seeded[0].id, "owner")) is None


# --- JWT ------------------------------------------------------------------
def test_verifier_rejects_bad_signature():
    token, _ = issue_admin(1, "owner")
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    with pytest.raises(AuthError):
        JwtTokenVerifier().verify(tampered)


def test_verifier_rejects_expired_token():
    iat = datetime.now(timezone.utc) - timedelta(hours=20)
    claims = {
        "sub": "owner",
        "store_id": 1,
        "role": "admin",
        "iat": iat,
        "exp": iat + timedelta(hours=1),
    }
    expired = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(AuthError):
        JwtTokenVerifier().verify(expired)


def test_table_token_claims():
    token, expires_in = issue_table(7, 42)
    ctx = JwtTokenVerifier().verify(token)
    assert ctx.role == "table" and ctx.table_id == 42 and ctx.store_id == 7
    assert ctx.subject == "table:42"
    assert expires_in == settings.table_token_expire_hours * 3600


# --- tenant isolation -----------------------------------------------------
def test_cross_store_admin_rejected(db, seeded):
    """Store A's admin cannot log into store B (username not in B)."""
    svc = AuthService(db)
    with pytest.raises(AuthError):
        svc.admin_login("b", "owner", "pw")


# --- table login ----------------------------------------------------------
def test_table_login_success(db, seeded):
    svc = AuthService(db)
    res = svc.table_login("a", "1", "tablepw")
    assert res.table_id is not None
    ctx = JwtTokenVerifier().verify(res.access_token)
    assert ctx.role == "table" and ctx.store_id == seeded[0].id


def test_table_login_failure(db, seeded):
    svc = AuthService(db)
    with pytest.raises(AuthError):
        svc.table_login("a", "1", "wrong")


# --- table setup (US-A4) --------------------------------------------------
def _admin_ctx(store_id: int) -> StoreContext:
    return StoreContext(store_id=store_id, role="admin", subject="owner")


def test_create_and_list_tables(db, seeded):
    svc = AuthService(db)
    ctx = _admin_ctx(seeded[0].id)
    created = svc.create_table(ctx, "5", "pw5")
    assert created.table_number == "5"
    numbers = {t.table_number for t in svc.list_tables(ctx)}
    assert {"1", "5"} <= numbers


def test_create_duplicate_number_rejected(db, seeded):
    svc = AuthService(db)
    ctx = _admin_ctx(seeded[0].id)
    with pytest.raises(ValidationError):
        svc.create_table(ctx, "1", "pw")  # '1' already exists in store A


def test_update_table_number_and_password(db, seeded):
    svc = AuthService(db)
    ctx = _admin_ctx(seeded[0].id)
    created = svc.create_table(ctx, "9", "pw9")
    updated = svc.update_table(ctx, created.id, table_number="99", password="new")
    assert updated.table_number == "99"
    # New password works for table login.
    assert svc.table_login("a", "99", "new").table_id == created.id


def test_update_missing_table_raises(db, seeded):
    svc = AuthService(db)
    with pytest.raises(NotFoundError):
        svc.update_table(_admin_ctx(seeded[0].id), 99999, table_number="x")


def test_update_to_existing_number_rejected(db, seeded):
    svc = AuthService(db)
    ctx = _admin_ctx(seeded[0].id)
    created = svc.create_table(ctx, "3", "pw3")
    with pytest.raises(ValidationError):
        svc.update_table(ctx, created.id, table_number="1")  # collides with table '1'
