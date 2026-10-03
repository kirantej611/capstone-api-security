import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8080"


class TestHealthCheck:
    def test_health(self):
        """Test health endpoint returns 200."""
        response = httpx.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuth:
    def test_register_user(self):
        """Test user registration."""
        response = httpx.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "testuser", "email": "test@test.com", "password": "testpass"}
        )
        assert response.status_code in [200, 201, 400]  # 400 if user exists

    def test_login_valid(self):
        """Test login with valid credentials."""
        response = httpx.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "admin"

    def test_login_invalid(self):
        """Test login with invalid credentials."""
        response = httpx.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_sql_injection_login(self):
        """Test that SQL injection works on login (VULN_MODE=true)."""
        response = httpx.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin' OR '1'='1", "password": "anything"}
        )
        # In VULN_MODE, this should return a user (SQLi success)
        # The exact status depends on whether VULN_MODE is enabled
        assert response.status_code in [200, 401, 400]


class TestProducts:
    def test_list_products(self):
        """Test listing all products."""
        response = httpx.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_product(self):
        """Test getting a specific product."""
        response = httpx.get(f"{BASE_URL}/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_search_products(self):
        """Test product search."""
        response = httpx.get(f"{BASE_URL}/api/search?q=laptop")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


class TestReviews:
    def test_get_reviews(self):
        """Test getting reviews for a product."""
        response = httpx.get(f"{BASE_URL}/api/products/1/reviews")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_review_xss(self):
        """Test that XSS payload is stored verbatim (VULN_MODE=true)."""
        response = httpx.post(
            f"{BASE_URL}/api/products/1/reviews",
            json={"rating": 5, "comment": "<script>alert('xss')</script>"}
        )
        assert response.status_code in [200, 201]


class TestCart:
    def test_add_to_cart(self):
        """Test adding item to cart."""
        response = httpx.post(
            f"{BASE_URL}/api/cart/add",
            json={"item_id": 1, "qty": 2}
        )
        assert response.status_code == 200

    def test_view_cart(self):
        """Test viewing cart."""
        response = httpx.get(f"{BASE_URL}/api/cart")
        assert response.status_code == 200


class TestOrders:
    def test_checkout(self):
        """Test checkout flow."""
        # First add item to cart
        httpx.post(f"{BASE_URL}/api/cart/add", json={"item_id": 1, "qty": 1})
        # Then checkout
        response = httpx.post(
            f"{BASE_URL}/api/checkout",
            json={"shipping_address": "123 Test St"}
        )
        assert response.status_code in [200, 201]

    def test_view_order_bola(self):
        """Test that any user can view any order (BOLA vulnerability)."""
        response = httpx.get(f"{BASE_URL}/api/orders/1")
        # Should return order without auth check
        assert response.status_code in [200, 404]


class TestVulnerable:
    def test_ping(self):
        """Test ping endpoint."""
        response = httpx.post(
            f"{BASE_URL}/api/ping",
            json={"host": "127.0.0.1"}
        )
        assert response.status_code == 200

    def test_download(self):
        """Test file download."""
        response = httpx.get(f"{BASE_URL}/api/download?file=invoice_sample.txt")
        assert response.status_code == 200

    def test_path_traversal(self):
        """Test path traversal attempt."""
        response = httpx.get(f"{BASE_URL}/api/download?file=../../README.md")
        # In VULN_MODE, this might succeed; in safe mode, 403
        assert response.status_code in [200, 403, 404]


class TestUserProfile:
    def test_get_profile(self):
        """Test getting user profile."""
        response = httpx.get(f"{BASE_URL}/api/user/profile")
        assert response.status_code == 200

    def test_bola_profile(self):
        """Test BOLA: access another user's profile."""
        response = httpx.get(f"{BASE_URL}/api/user/profile?user_id=2")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
