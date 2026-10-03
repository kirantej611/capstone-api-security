"""
Anomalous Traffic Generator

Simulates anomalous behaviour that looks suspicious even without matching
known attack signatures — designed to trigger the Autoencoder anomaly detector:

  1. Credential Stuffing — rapid-fire login attempts with many username/password combos
  2. Rapid Enumeration — scanning product IDs sequentially at high speed
  3. Aggressive Scraping — hammering product listings with varying user agents

These patterns are characterised by:
  - Very high request rate from a single IP
  - Repetitive patterns with slight variations
  - Unusual parameter distributions
"""

import random
import itertools

import httpx

from payloads import COMMON_USERNAMES, COMMON_PASSWORDS
from config import CREDENTIAL_STUFFING_BATCH_SIZE


SCRAPER_USER_AGENTS = [
    "python-requests/2.31.0",
    "curl/7.88.1",
    "Wget/1.21",
    "Scrapy/2.11",
    "Go-http-client/1.1",
    "Java/17.0.1",
    "libwww-perl/6.67",
    "PhantomJS/2.1.1",
    "HeadlessChrome/120.0",
]


class AnomalousTrafficGenerator:
    """Generates anomalous traffic patterns (credential stuffing, enumeration, scraping)."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        # Pre-build credential combos and cycle through them
        combos = list(itertools.product(COMMON_USERNAMES, COMMON_PASSWORDS))
        random.shuffle(combos)
        self._credential_iter = itertools.cycle(combos)
        self._enum_counter = 0

    # ═══════════════════════════════════════════════════════
    # CREDENTIAL STUFFING
    # ═══════════════════════════════════════════════════════

    async def credential_stuffing_single(self, client: httpx.AsyncClient) -> dict:
        """
        Try one username/password combination against /api/login.

        This simulates an attacker cycling through leaked credential databases.
        The anomaly signal comes from the sheer volume + speed + failure rate.
        """
        username, password = next(self._credential_iter)
        resp = await client.post(
            f"{self.base_url}/api/login",
            json={"username": username, "password": password},
        )
        return {
            "action": "credential_stuffing",
            "anomaly_type": "Credential Stuffing",
            "method": "POST",
            "path": "/api/login",
            "status": resp.status_code,
            "detail": f"Stuffing: {username}:{password[:8]}***",
        }

    async def credential_stuffing_burst(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Fire a burst of credential stuffing attempts (batch).
        Returns a list of results for the entire burst.
        """
        results = []
        batch_size = min(CREDENTIAL_STUFFING_BATCH_SIZE, 50)
        for _ in range(batch_size):
            result = await self.credential_stuffing_single(client)
            results.append(result)
        return results

    # ═══════════════════════════════════════════════════════
    # RAPID ENUMERATION
    # ═══════════════════════════════════════════════════════

    async def enumerate_products(self, client: httpx.AsyncClient) -> dict:
        """
        Sequentially scan product IDs at high speed.

        Normal users view products randomly; an attacker scans sequentially
        (1, 2, 3, ..., 100, 101, ...) to discover hidden or unlisted items.
        """
        self._enum_counter += 1
        product_id = self._enum_counter
        resp = await client.get(f"{self.base_url}/api/products/{product_id}")
        return {
            "action": "enumerate_products",
            "anomaly_type": "Rapid Enumeration",
            "method": "GET",
            "path": f"/api/products/{product_id}",
            "status": resp.status_code,
            "detail": f"Sequential scan: product #{product_id}",
        }

    async def enumerate_orders(self, client: httpx.AsyncClient) -> dict:
        """
        Enumerate order IDs to find other users' orders (BOLA).
        """
        order_id = random.randint(1, 1000)
        resp = await client.get(f"{self.base_url}/api/orders/{order_id}")
        return {
            "action": "enumerate_orders",
            "anomaly_type": "Rapid Enumeration",
            "method": "GET",
            "path": f"/api/orders/{order_id}",
            "status": resp.status_code,
            "detail": f"Order enumeration: order #{order_id}",
        }

    # ═══════════════════════════════════════════════════════
    # AGGRESSIVE SCRAPING
    # ═══════════════════════════════════════════════════════

    async def aggressive_scrape(self, client: httpx.AsyncClient) -> dict:
        """
        Rapidly scrape product listings with suspicious user agents.

        Anomaly signals: bot user-agent, high frequency, paginating exhaustively.
        """
        page = random.randint(1, 50)
        ua = random.choice(SCRAPER_USER_AGENTS)
        resp = await client.get(
            f"{self.base_url}/api/products",
            params={"page": page, "limit": 100},
            headers={"User-Agent": ua},
        )
        return {
            "action": "aggressive_scrape",
            "anomaly_type": "Aggressive Scraping",
            "method": "GET",
            "path": f"/api/products?page={page}&limit=100",
            "status": resp.status_code,
            "detail": f"Scraping page {page} (UA: {ua[:20]}...)",
        }

    # ═══════════════════════════════════════════════════════
    # RANDOM ANOMALY SELECTOR
    # ═══════════════════════════════════════════════════════

    async def generate_one(self, client: httpx.AsyncClient) -> dict:
        """
        Generate a single anomalous traffic request.

        Weighted towards credential stuffing (the primary anomalous scenario):
          - 50% Credential Stuffing
          - 20% Product Enumeration
          - 15% Order Enumeration
          - 15% Aggressive Scraping
        """
        actions = [
            (self.credential_stuffing_single, 50),
            (self.enumerate_products, 20),
            (self.enumerate_orders, 15),
            (self.aggressive_scrape, 15),
        ]
        funcs, weights = zip(*actions)
        chosen = random.choices(funcs, weights=weights, k=1)[0]

        try:
            return await chosen(client)
        except Exception as exc:
            return {
                "action": chosen.__name__,
                "anomaly_type": "Unknown",
                "method": "?",
                "path": "?",
                "status": 0,
                "detail": f"Error: {exc}",
            }
