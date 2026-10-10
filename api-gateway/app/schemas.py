"""
Pydantic schemas for the API Gateway.

These models define the data contracts between the gateway and other services
(ML Engine, Security Backend, Kafka topics, Dashboard API).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ──

class RiskLevel(str, Enum):
    """Risk severity levels returned by the ML engine."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GatewayAction(str, Enum):
    """Action taken by the gateway on a request."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    RATE_LIMIT = "RATE_LIMIT"
    FLAG = "FLAG"


class BlockReason(str, Enum):
    """Reason a request was blocked."""
    ML_THREAT_DETECTED = "ML_THREAT_DETECTED"
    IP_BLOCKLISTED = "IP_BLOCKLISTED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    ML_ENGINE_UNAVAILABLE = "ML_ENGINE_UNAVAILABLE"


# ── ML Engine Schemas (mirrors ml-engine/api/main.py contracts) ──

class MLPredictRequest(BaseModel):
    """Request payload sent to the ML engine's /predict endpoint."""
    url: str
    method: str
    body: str = ""
    headers: Dict[str, str] = {}


class MLPredictResponse(BaseModel):
    """Response from the ML engine's /predict endpoint."""
    anomaly_score: float
    is_anomalous: bool
    threat_type: str
    threat_confidence: float
    all_probabilities: Dict[str, float]
    risk_level: str
    feature_importance: Dict[str, float]


# ── Kafka Event Schemas ──

class RequestMetadata(BaseModel):
    """
    Metadata extracted from an intercepted HTTP request.
    Published to Kafka topic `api.requests.raw` for async analysis and logging.
    """
    request_id: str = Field(description="Unique correlation ID for this request")
    timestamp: str = Field(description="ISO-8601 timestamp of interception")
    client_ip: str
    method: str
    url: str
    path: str
    query_params: Dict[str, str] = {}
    headers: Dict[str, str] = {}
    body: str = ""
    content_type: Optional[str] = None
    user_agent: Optional[str] = None


class GatewayVerdict(BaseModel):
    """
    The gateway's final decision on a request.
    Published to Kafka topic `api.verdicts` for the Security Backend to consume.
    """
    request_id: str = Field(description="Correlation ID linking to RequestMetadata")
    timestamp: str = Field(description="ISO-8601 timestamp of the verdict")
    client_ip: str
    method: str
    path: str
    action: GatewayAction
    block_reason: Optional[BlockReason] = None

    # ML Results (None if ML engine was skipped or unreachable)
    anomaly_score: Optional[float] = None
    is_anomalous: Optional[bool] = None
    threat_type: Optional[str] = None
    threat_confidence: Optional[float] = None
    risk_level: Optional[str] = None
    feature_importance: Optional[Dict[str, float]] = None
    all_probabilities: Optional[Dict[str, float]] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    query_params: Optional[Dict[str, str]] = None

    # Timing
    ml_latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None


# ── Dashboard / Metrics Schemas ──

class GatewayStats(BaseModel):
    """Real-time gateway statistics exposed via the /stats endpoint."""
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    rate_limited_requests: int = 0
    flagged_requests: int = 0
    avg_ml_latency_ms: float = 0.0
    active_blocked_ips: int = 0
    uptime_seconds: float = 0.0
    requests_per_second: float = 0.0


class RecentVerdict(BaseModel):
    """A recent verdict for the live feed on the dashboard."""
    request_id: str
    timestamp: str
    client_ip: str
    method: str
    path: str
    action: GatewayAction
    threat_type: Optional[str] = None
    risk_level: Optional[str] = None
    anomaly_score: Optional[float] = None
    is_anomalous: Optional[bool] = None
    block_reason: Optional[BlockReason] = None
    threat_confidence: Optional[float] = None
    all_probabilities: Optional[Dict[str, float]] = None
    feature_importance: Optional[Dict[str, float]] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    query_params: Optional[Dict[str, str]] = None
    ml_latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    service: str = "api-gateway"
    redis_connected: bool = False
    kafka_connected: bool = False
    ml_engine_connected: bool = False
    uptime_seconds: float = 0.0
