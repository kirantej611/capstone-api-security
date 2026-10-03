"""
Normal Traffic Generator

Simulates realistic e-commerce browsing behaviour:
  - Browsing products (list, detail, search)
  - Reading reviews
  - Adding items to cart and checking out
  - Viewing user profile and order history

All requests hit the API Gateway (port 8080), which proxies them to
the victim e-commerce backend (port 8081).
"""

import random
from typing import Optional

import httpx

from payloads import NORMAL_SEARCH_TERMS, NORMAL_REVIEW_COMMENTS


class NormalTrafficGenerator:
    """Generates legitimate e-commerce browsing traffic."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._user_id: Optional[int] = None

    # ── Helper ──

    def _auth_headers(self) -> dict:
        """Return Authorization header if we have a token."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    # ── Traffic actions ──

    async def browse_products(self, client: httpx.AsyncClient) -> dict:
        """GET /api/products — list all products."""
        page = random.randint(1, 3)
        resp = await client.get(
            f"{self.base_url}/api/products",
            params={"page": page, "limit": 20},
        )
        return {
            "action": "browse_products",
            "method": "GET",
            "path": f"/api/products?page={page}",
            "status": resp.status_code,
            "detail": f"Listed products (page {page})",
        }

    async def view_product(self, client: httpx.AsyncClient) -> dict:
        """GET /api/products/{id} — view a single product."""
        product_id = random.randint(1, 12)
        resp = await client.get(f"{self.base_url}/api/products/{product_id}")
        return {
            "action": "view_product",
            "method": "GET",
            "path": f"/api/products/{product_id}",
            "status": resp.status_code,
            "detail": f"Viewed product #{product_id}",
        }

    async def search_products(self, client: httpx.AsyncClient) -> dict:
        """GET /api/search?q= — search with a normal term."""
        term = random.choice(NORMAL_SEARCH_TERMS)
        resp = await client.get(
            f"{self.base_url}/api/search",
            params={"q": term},
        )
        return {
            "action": "search_products",
            "method": "GET",
            "path": f"/api/search?q={term}",
            "status": resp.status_code,
            "detail": f"Searched for '{term}'",
        }

    async def read_reviews(self, client: httpx.AsyncClient) -> dict:
        """GET /api/products/{id}/reviews — read product reviews."""
        product_id = random.randint(1, 12)
        resp = await client.get(f"{self.base_url}/api/products/{product_id}/reviews")
        return {
            "action": "read_reviews",
            "method": "GET",
            "path": f"/api/products/{product_id}/reviews",
            "status": resp.status_code,
            "detail": f"Read reviews for product #{product_id}",
        }

    async def write_review(self, client: httpx.AsyncClient) -> dict:
        """POST /api/products/{id}/reviews — write a legitimate review."""
        product_id = random.randint(1, 12)
        comment = random.choice(NORMAL_REVIEW_COMMENTS)
        rating = random.randint(3, 5)
        resp = await client.post(
            f"{self.base_url}/api/products/{product_id}/reviews",
            json={"rating": rating, "comment": comment},
            headers=self._auth_headers(),
        )
        return {
            "action": "write_review",
            "method": "POST",
            "path": f"/api/products/{product_id}/reviews",
            "status": resp.status_code,
            "detail": f"Reviewed product #{product_id} ({rating}★)",
        }

    async def login_legitimate(self, client: httpx.AsyncClient) -> dict:
        """POST /api/login — login with valid credentials."""
        creds = random.choice([
            {"username": "user1", "password": "password123"},
            {"username": "user2", "password": "password456"},
        ])
        resp = await client.post(
            f"{self.base_url}/api/login",
            json=creds,
        )
        if resp.status_code == 200:
            data = resp.json()
            self._token = data.get("token")
            self._user_id = data.get("user_id")
        return {
            "action": "login",
            "method": "POST",
            "path": "/api/login",
            "status": resp.status_code,
            "detail": f"Logged in as {creds['username']}",
        }

    async def add_to_cart(self, client: httpx.AsyncClient) -> dict:
        """POST /api/cart/add — add a random product to cart."""
        item_id = random.randint(1, 12)
        qty = random.randint(1, 3)
        resp = await client.post(
            f"{self.base_url}/api/cart/add",
            json={"item_id": item_id, "qty": qty},
            headers=self._auth_headers(),
        )
        return {
            "action": "add_to_cart",
            "method": "POST",
            "path": "/api/cart/add",
            "status": resp.status_code,
            "detail": f"Added product #{item_id} (qty={qty}) to cart",
        }

    async def view_cart(self, client: httpx.AsyncClient) -> dict:
        """GET /api/cart — view cart contents."""
        resp = await client.get(
            f"{self.base_url}/api/cart",
            headers=self._auth_headers(),
        )
        return {
            "action": "view_cart",
            "method": "GET",
            "path": "/api/cart",
            "status": resp.status_code,
            "detail": "Viewed cart",
        }

    async def checkout(self, client: httpx.AsyncClient) -> dict:
        """POST /api/checkout — place an order."""
        resp = await client.post(
            f"{self.base_url}/api/checkout",
            json={"shipping_address": "123 Normal Street, Safe City"},
            headers=self._auth_headers(),
        )
        return {
            "action": "checkout",
            "method": "POST",
            "path": "/api/checkout",
            "status": resp.status_code,
            "detail": "Placed order",
        }

    async def view_profile(self, client: httpx.AsyncClient) -> dict:
        """GET /api/user/profile — view user profile."""
        resp = await client.get(
            f"{self.base_url}/api/user/profile",
            headers=self._auth_headers(),
        )
        return {
            "action": "view_profile",
            "method": "GET",
            "path": "/api/user/profile",
            "status": resp.status_code,
            "detail": "Viewed profile",
        }

    async def health_check(self, client: httpx.AsyncClient) -> dict:
        """GET /api/health — health check."""
        resp = await client.get(f"{self.base_url}/api/health")
        return {
            "action": "health_check",
            "method": "GET",
            "path": "/api/health",
            "status": resp.status_code,
            "detail": "Health check",
        }

    async def generate_one(self, client: httpx.AsyncClient) -> dict:
        """
        Generate a single random normal traffic request.

        Weighted towards common browsing patterns:
          - 30% browse products
          - 20% view single product
          - 15% search
          - 10% read reviews
          - 5%  write review
          - 5%  login
          - 5%  add to cart
          - 3%  view cart
          - 2%  checkout
          - 3%  view profile
          - 2%  health check
        """
        actions = [
            (self.browse_products, 30),
            (self.view_product, 20),
            (self.search_products, 15),
            (self.read_reviews, 10),
            (self.write_review, 5),
            (self.login_legitimate, 5),
            (self.add_to_cart, 5),
            (self.view_cart, 3),
            (self.checkout, 2),
            (self.view_profile, 3),
            (self.health_check, 2),
        ]
        funcs, weights = zip(*actions)
        chosen = random.choices(funcs, weights=weights, k=1)[0]

        try:
            return await chosen(client)
        except Exception as exc:
            return {
                "action": chosen.__name__,
                "method": "?",
                "path": "?",
                "status": 0,
                "detail": f"Error: {exc}",
            }
