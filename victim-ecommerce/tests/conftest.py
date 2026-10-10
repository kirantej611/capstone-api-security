import os

os.environ["SKIP_DB_INIT"] = "1"
os.environ["VULN_MODE"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.fakes import FakePool, FakeStore


@pytest.fixture
def store():
    return FakeStore()


@pytest.fixture
def client(store, monkeypatch):
    monkeypatch.setattr("app.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.auth.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.cart.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.orders.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.reviews.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.products.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.user.database.pool", FakePool(store))
    monkeypatch.setattr("app.routes.auth.VULN_MODE", False)
    monkeypatch.setattr("app.routes.cart.VULN_MODE", False)
    monkeypatch.setattr("app.routes.orders.VULN_MODE", False)
    monkeypatch.setattr("app.routes.reviews.VULN_MODE", False)
    monkeypatch.setattr("app.routes.products.VULN_MODE", False)
    monkeypatch.setattr("app.routes.user.VULN_MODE", False)
    monkeypatch.setattr("app.auth_utils.VULN_MODE", False)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
