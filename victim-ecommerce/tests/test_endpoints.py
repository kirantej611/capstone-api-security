"""
Live integration tests against a running gateway (default http://localhost:8080).

These are skipped unless RUN_LIVE_API_TESTS=1 because they require the
compose stack (or equivalent) to already be available.
"""
import os

import httpx
import pytest

BASE_URL = os.getenv("LIVE_API_BASE_URL", "http://localhost:8080")

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_API_TESTS") != "1",
    reason="Set RUN_LIVE_API_TESTS=1 to run live gateway integration tests",
)


class TestHealthCheck:
    def test_health(self):
        response = httpx.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuth:
    def test_login_valid(self):
        response = httpx.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "admin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "admin"


class TestProducts:
    def test_list_products(self):
        response = httpx.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
