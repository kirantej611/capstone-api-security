import asyncio
from unittest.mock import AsyncMock

from fastapi import Request

from app.main import ChatbotRouter
from app.proxy_handler import _dashboard_request_body, _get_client_ip
from app.services.redis_service import RedisService


def make_request(peer_ip: str, forwarded_ip: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-forwarded-for", forwarded_ip.encode())],
            "client": (peer_ip, 12345),
        }
    )


def test_dashboard_body_replaces_unparseable_content():
    assert _dashboard_request_body("password=secret") == (
        "[REDACTED: unparseable request body]"
    )


def test_client_ip_ignores_forwarded_header_from_untrusted_peer(monkeypatch):
    monkeypatch.setattr("app.proxy_handler.settings.trusted_proxy_ips", "192.0.2.1/32")

    assert _get_client_ip(make_request("198.51.100.20", "203.0.113.7")) == "198.51.100.20"


def test_client_ip_accepts_forwarded_header_from_trusted_peer(monkeypatch):
    monkeypatch.setattr("app.proxy_handler.settings.trusted_proxy_ips", "192.0.2.1/32")

    assert _get_client_ip(make_request("192.0.2.1", "203.0.113.7")) == "203.0.113.7"


def test_chatbot_rate_limit_prunes_expired_clients(monkeypatch):
    monkeypatch.setattr("app.main.time.time", lambda: 100)
    router = ChatbotRouter()
    router.rate_limits = {"expired": [39], "active": [99]}

    assert router._check_rate_limit("new") is True
    assert router.rate_limits == {"active": [99], "new": [100]}


def test_chatbot_reports_newest_threat_first():
    router = ChatbotRouter()
    router.get_live_cluster_data = AsyncMock(
        return_value={"recent_threats": ["newest incident", "older incident"]}
    )

    reply = asyncio.run(router._handle_threats("threat"))

    assert "newest incident" in reply
    assert "older incident" not in reply


def test_burst_limit_sets_expiry_only_for_new_counter():
    service = RedisService()
    service._client = AsyncMock()
    service._client.incr = AsyncMock(return_value=1)
    service._client.expire = AsyncMock()

    allowed, count = asyncio.run(service.check_burst_limit("192.0.2.20"))

    assert (allowed, count) == (True, 1)
    service._client.expire.assert_awaited_once()


def test_burst_limit_does_not_extend_existing_counter_expiry():
    service = RedisService()
    service._client = AsyncMock()
    service._client.incr = AsyncMock(return_value=2)
    service._client.expire = AsyncMock()

    asyncio.run(service.check_burst_limit("192.0.2.20"))

    service._client.expire.assert_not_awaited()
