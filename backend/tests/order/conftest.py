"""Shared fixtures for U3 order tests."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.database import Base
from app.common.models import Store, Table  # noqa: F401 - register tables
from app.order import models as _order_models  # noqa: F401 - register order tables


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # seed a store so store_id FK is satisfiable
        session.add(Store(id=1, code="s1", name="Store 1"))
        session.add(Store(id=2, code="s2", name="Store 2"))
        session.flush()
        yield session
    finally:
        session.close()
