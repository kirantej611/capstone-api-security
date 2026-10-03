"""
Tests for the API Gateway.

Uses FastAPI's TestClient (synchronous) and pytest.
Mocks external services (Redis, Kafka, ML Engine) to test the gateway logic in isolation.
"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import GatewayAction, MLPredictResponse


# ── Fixtures ──

@pytest.fixture
def client():
    """Create a test client with mocked external services."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Health & Admin Tests ──

class TestHealthEndpoints:
    """Test the /gateway/* admin endpoints."""

    def test_health_endpoint(self, client):
        """Health endpoint should return 200 with service info."""
        resp = client.get("/gateway/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "redis_connected" in data
        assert "kafka_connected" in data
        assert "ml_engine_connected" in data

    def test_stats_endpoint(self, client):
        """Stats endpoint should return gateway metrics."""
        resp = client.get("/gateway/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "allowed_requests" in data
        assert "blocked_requests" in data
        assert "requests_per_second" in data

    def test_recent_verdicts_endpoint(self, client):
        """Recent verdicts endpoint should return a list."""
        resp = client.get("/gateway/verdicts/recent")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_blocklist_endpoint(self, client):
        """Blocklist endpoint should return blocked IPs."""
        resp = client.get("/gateway/blocklist")
        assert resp.status_code == 200
        data = resp.json()
        assert "blocked_ips" in data
        assert "count" in data


# ── Proxy Pipeline Tests ──

class TestProxyPipeline:
    """Test the main request processing pipeline."""

    @patch("app.proxy_handler.redis_service")
    @patch("app.proxy_handler.kafka_service")
    @patch("app.proxy_handler.ml_engine_client")
    def test_allow_normal_request(self, mock_ml, mock_kafka, mock_redis, client):
        """A normal request with a clean ML verdict should be forwarded."""
        # Mock: not blocklisted, not rate-limited
        mock_redis.is_ip_blocked = AsyncMock(return_value=False)
        mock_redis.check_rate_limit = AsyncMock(return_value=(True, 1))

        # Mock: ML says normal
        mock_prediction = MLPredictResponse(
            anomaly_score=0.01,
            is_anomalous=False,
            threat_type="Normal",
            threat_confidence=0.95,
            all_probabilities={"Normal": 0.95, "SQLi": 0.02, "XSS": 0.01, "PathTraversal": 0.01, "CommandInjection": 0.01},
            risk_level="LOW",
            feature_importance={"url_length": 0.1},
        )
        mock_ml.predict = AsyncMock(return_value=(mock_prediction, 5.0))

        # Mock Kafka
        mock_kafka.publish_request_metadata = AsyncMock()
        mock_kafka.publish_verdict = AsyncMock()

        # The upstream is not running in tests, so we expect a 502 (upstream unreachable)
        # but the key assertion is that the gateway did NOT block the request (no 403)
        resp = client.get("/api/products")
        # Should NOT be 403 (blocked) or 429 (rate-limited)
        assert resp.status_code != 403
        assert resp.status_code != 429

    @patch("app.proxy_handler.redis_service")
    @patch("app.proxy_handler.kafka_service")
    @patch("app.proxy_handler.ml_engine_client")
    def test_block_blocklisted_ip(self, mock_ml, mock_kafka, mock_redis, client):
        """A request from a blocklisted IP should be blocked (403)."""
        mock_redis.is_ip_blocked = AsyncMock(return_value=True)
        mock_kafka.publish_request_metadata = AsyncMock()
        mock_kafka.publish_verdict = AsyncMock()

        resp = client.get("/api/products")
        assert resp.status_code == 403
        data = resp.json()
        assert data["reason"] == "ip_blocklisted"

    @patch("app.proxy_handler.redis_service")
    @patch("app.proxy_handler.kafka_service")
    @patch("app.proxy_handler.ml_engine_client")
    def test_rate_limit_exceeded(self, mock_ml, mock_kafka, mock_redis, client):
        """A request exceeding rate limit should return 429."""
        mock_redis.is_ip_blocked = AsyncMock(return_value=False)
        mock_redis.check_rate_limit = AsyncMock(return_value=(False, 101))
        mock_redis.block_ip = AsyncMock()
        mock_kafka.publish_request_metadata = AsyncMock()
        mock_kafka.publish_verdict = AsyncMock()

        resp = client.get("/api/products")
        assert resp.status_code == 429
        data = resp.json()
        assert data["reason"] == "rate_limit_exceeded"

    @patch("app.proxy_handler.redis_service")
    @patch("app.proxy_handler.kafka_service")
    @patch("app.proxy_handler.ml_engine_client")
    def test_block_critical_threat(self, mock_ml, mock_kafka, mock_redis, client):
        """A CRITICAL threat should be blocked (403)."""
        mock_redis.is_ip_blocked = AsyncMock(return_value=False)
        mock_redis.check_rate_limit = AsyncMock(return_value=(True, 1))
        mock_redis.block_ip = AsyncMock()

        mock_prediction = MLPredictResponse(
            anomaly_score=0.95,
            is_anomalous=True,
            threat_type="SQL_Injection",
            threat_confidence=0.92,
            all_probabilities={"Normal": 0.03, "SQLi": 0.92, "XSS": 0.02, "PathTraversal": 0.02, "CommandInjection": 0.01},
            risk_level="CRITICAL",
            feature_importance={"num_sql_keywords": 5.0, "num_special_chars": 3.2},
        )
        mock_ml.predict = AsyncMock(return_value=(mock_prediction, 8.0))
        mock_kafka.publish_request_metadata = AsyncMock()
        mock_kafka.publish_verdict = AsyncMock()

        resp = client.get("/api/login?username=admin' OR '1'='1")
        assert resp.status_code == 403
        data = resp.json()
        assert data["reason"] == "threat_detected"
        assert "SQL_Injection" in data["detail"]


# ── Schema Tests ──

class TestSchemas:
    """Test Pydantic schema validation."""

    def test_ml_predict_response_parsing(self):
        """MLPredictResponse should parse valid data."""
        data = {
            "anomaly_score": 0.5,
            "is_anomalous": True,
            "threat_type": "XSS",
            "threat_confidence": 0.8,
            "all_probabilities": {"Normal": 0.1, "XSS": 0.8, "SQLi": 0.1},
            "risk_level": "HIGH",
            "feature_importance": {"num_xss_keywords": 3.0},
        }
        resp = MLPredictResponse(**data)
        assert resp.threat_type == "XSS"
        assert resp.risk_level == "HIGH"

    def test_gateway_action_enum(self):
        """GatewayAction enum values should be correct."""
        assert GatewayAction.ALLOW == "ALLOW"
        assert GatewayAction.BLOCK == "BLOCK"
        assert GatewayAction.RATE_LIMIT == "RATE_LIMIT"


# ── Config Tests ──

class TestConfig:
    """Test configuration loading."""

    def test_default_settings(self):
        """Settings should load with sensible defaults."""
        from app.config import settings
        assert settings.gateway_port == 8080
        assert settings.rate_limit_max_requests == 100
        assert settings.block_on_ml_failure is False
        assert settings.risk_threshold_block == "HIGH"
