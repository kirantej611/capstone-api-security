"""
Core proxy handler for the API Gateway.

This is the central request processing pipeline:
  1. Extract client IP & generate correlation ID
  2. Check Redis blocklist → BLOCK if listed
  3. Check rate limit → RATE_LIMIT if exceeded
  4. Call ML Engine for threat prediction
  5. Apply security policy (block / flag / allow based on risk level)
  6. Publish events to Kafka (request metadata + verdict)
  7. Forward allowed requests to the upstream e-commerce backend
  8. Record metrics for the dashboard
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

import httpx
from fastapi import Request, Response

from app.config import settings
from app.logging_config import get_logger
from app.metrics import metrics_tracker
from app.schemas import (
    BlockReason,
    GatewayAction,
    GatewayVerdict,
    MLPredictResponse,
    RequestMetadata,
    RiskLevel,
)
from app.services.kafka_service import kafka_service
from app.services.ml_engine_client import ml_engine_client
from app.services.redis_service import redis_service

logger = get_logger("proxy_handler")

# Risk levels ordered by severity for comparison
RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}

SENSITIVE_FIELD_NAMES = {
    "password",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "authorization",
}
SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "set-cookie",
}
MAX_DASHBOARD_BODY_LENGTH = 16_384


def _redact_sensitive_values(value):
    """Mask common credentials before request content is included in dashboard verdicts."""
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if key.lower() in SENSITIVE_FIELD_NAMES
                else _redact_sensitive_values(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    return value


def _dashboard_request_body(body: str) -> str:
    try:
        body = json.dumps(_redact_sensitive_values(json.loads(body)), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
    if len(body) > MAX_DASHBOARD_BODY_LENGTH:
        return body[:MAX_DASHBOARD_BODY_LENGTH] + "\n[TRUNCATED]"
    return body


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP, honoring X-Forwarded-For if present.
    Falls back to the direct connection IP.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _should_block_by_risk(risk_level_str: str) -> bool:
    """
    Determine if a request should be blocked based on the configured risk threshold.

    Example: if threshold is HIGH, then HIGH and CRITICAL are blocked.
    """
    try:
        risk = RiskLevel(risk_level_str)
        threshold = RiskLevel(settings.risk_threshold_block)
    except ValueError:
        return False
    return RISK_ORDER.get(risk, 0) >= RISK_ORDER.get(threshold, 2)


async def _build_request_metadata(
    request: Request, request_id: str, client_ip: str, body: str
) -> RequestMetadata:
    """Build a RequestMetadata event from a FastAPI Request."""
    return RequestMetadata(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        client_ip=client_ip,
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        query_params=dict(request.query_params),
        headers={k: v for k, v in request.headers.items()},
        body=body,
        content_type=request.headers.get("content-type"),
        user_agent=request.headers.get("user-agent"),
    )


def _build_verdict(
    request_id: str,
    client_ip: str,
    method: str,
    path: str,
    action: GatewayAction,
    block_reason: Optional[BlockReason],
    prediction: Optional[MLPredictResponse],
    ml_latency_ms: float,
    total_latency_ms: float,
    threat_type_override: Optional[str] = None,
    risk_level_override: Optional[str] = None,
    is_anomalous_override: Optional[bool] = None,
    request_metadata: Optional[RequestMetadata] = None,
) -> GatewayVerdict:
    """Build a GatewayVerdict event."""
    verdict = GatewayVerdict(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        client_ip=client_ip,
        method=method,
        path=path,
        action=action,
        block_reason=block_reason,
        ml_latency_ms=round(ml_latency_ms, 2),
        total_latency_ms=round(total_latency_ms, 2),
    )
    if prediction:
        verdict.anomaly_score = prediction.anomaly_score
        verdict.is_anomalous = prediction.is_anomalous
        verdict.threat_type = prediction.threat_type
        verdict.threat_confidence = prediction.threat_confidence
        verdict.risk_level = prediction.risk_level
        verdict.feature_importance = prediction.feature_importance
        verdict.all_probabilities = prediction.all_probabilities
    if threat_type_override is not None:
        verdict.threat_type = threat_type_override
    if risk_level_override is not None:
        verdict.risk_level = risk_level_override
    if is_anomalous_override is not None:
        verdict.is_anomalous = is_anomalous_override
    if request_metadata is not None:
        verdict.headers = {
            key: value
            for key, value in request_metadata.headers.items()
            if key.lower() not in SENSITIVE_HEADER_NAMES
        }
        verdict.body = _dashboard_request_body(request_metadata.body)
        verdict.query_params = {
            key: (
                "[REDACTED]"
                if key.lower() in SENSITIVE_FIELD_NAMES
                else value
            )
            for key, value in request_metadata.query_params.items()
        }
    return verdict


def _make_block_response(
    request_id: str, reason: str, detail: str, status_code: int = 403
) -> Response:
    """Create a JSON error response for blocked requests."""
    import json

    body = json.dumps(
        {
            "error": "request_blocked",
            "reason": reason,
            "detail": detail,
            "request_id": request_id,
        }
    )
    return Response(
        content=body,
        status_code=status_code,
        media_type="application/json",
    )


async def handle_request(request: Request) -> Response:
    """
    Main request processing pipeline.

    This function is the core of the API Gateway. Every incoming request
    passes through this handler.
    """
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())
    client_ip = _get_client_ip(request)

    logger.info(
        "request_received",
        request_id=request_id,
        client_ip=client_ip,
        method=request.method,
        path=request.url.path,
    )

    # ── Step 1: Read the request body ──
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8", errors="replace")
    except Exception:
        body_str = ""

    # ── Step 2: Publish request metadata to Kafka (async, non-blocking) ──
    metadata = await _build_request_metadata(request, request_id, client_ip, body_str)
    # Fire-and-forget to Kafka (don't slow down the request)
    try:
        await kafka_service.publish_request_metadata(metadata)
    except Exception as exc:
        logger.warning("kafka_metadata_publish_failed", error=str(exc))

    # ── Step 3: Check IP blocklist ──
    if await redis_service.is_ip_blocked(client_ip):
        logger.warning("request_blocked_blocklist", request_id=request_id, ip=client_ip)
        verdict = _build_verdict(
            request_id, client_ip, request.method, request.url.path,
            GatewayAction.BLOCK, BlockReason.IP_BLOCKLISTED,
            None, 0.0, (time.perf_counter() - start_time) * 1000,
            request_metadata=metadata,
        )
        await _publish_and_record(verdict)
        return _make_block_response(
            request_id, "ip_blocklisted",
            "Your IP has been temporarily blocked due to suspicious activity.",
        )

    # ── Step 4: Check rate limit ──
    is_allowed, current_count = await redis_service.check_rate_limit(client_ip)
    if not is_allowed:
        logger.warning(
            "request_rate_limited",
            request_id=request_id,
            ip=client_ip,
            count=current_count,
        )
        # Auto-block IPs that exceed 3x the rate limit (aggressive behavior)
        if current_count > settings.rate_limit_max_requests * 3:
            await redis_service.block_ip(client_ip, reason="excessive_rate_limit_violations")

        verdict = _build_verdict(
            request_id, client_ip, request.method, request.url.path,
            GatewayAction.RATE_LIMIT, BlockReason.RATE_LIMIT_EXCEEDED,
            None, 0.0, (time.perf_counter() - start_time) * 1000,
            request_metadata=metadata,
        )
        await _publish_and_record(verdict)
        return _make_block_response(
            request_id, "rate_limit_exceeded",
            f"Too many requests. Limit: {settings.rate_limit_max_requests} per {settings.rate_limit_window}s.",
            status_code=429,
        )

    # Short-window detection catches bursts well below the broad per-minute cap.
    is_burst_allowed, burst_count = await redis_service.check_burst_limit(client_ip)
    if not is_burst_allowed:
        logger.warning(
            "request_burst_limited",
            request_id=request_id,
            ip=client_ip,
            count=burst_count,
        )
        await redis_service.block_ip(
            client_ip,
            reason="anomaly_burst",
        )
        verdict = _build_verdict(
            request_id, client_ip, request.method, request.url.path,
            GatewayAction.RATE_LIMIT, BlockReason.RATE_LIMIT_EXCEEDED,
            None, 0.0, (time.perf_counter() - start_time) * 1000,
            threat_type_override="AnomalyBurst",
            risk_level_override="HIGH",
            is_anomalous_override=True,
            request_metadata=metadata,
        )
        await _publish_and_record(verdict)
        response = _make_block_response(
            request_id, "anomaly_burst",
            f"Too many requests. Limit: {settings.burst_limit_max_requests} "
            f"per {settings.burst_limit_window}s.",
            status_code=429,
        )
        response.headers["x-gateway-action"] = GatewayAction.RATE_LIMIT.value
        response.headers["x-gateway-threat-type"] = "AnomalyBurst"
        return response

    # ── Step 5: ML Engine threat prediction ──
    prediction: Optional[MLPredictResponse] = None
    ml_latency_ms = 0.0

    prediction, ml_latency_ms = await ml_engine_client.predict(
        url=str(request.url),
        method=request.method,
        body=body_str,
        headers=dict(request.headers),
    )

    # ── Step 6: Apply security policy ──
    action = GatewayAction.ALLOW
    block_reason = None

    if prediction is None:
        # ML engine is unavailable
        if settings.block_on_ml_failure:
            action = GatewayAction.BLOCK
            block_reason = BlockReason.ML_ENGINE_UNAVAILABLE
            logger.warning("request_blocked_ml_unavailable", request_id=request_id)
        else:
            logger.info("ml_unavailable_allowing", request_id=request_id)
    else:
        # We have a prediction — apply risk threshold
        if prediction.is_anomalous and _should_block_by_risk(prediction.risk_level):
            action = GatewayAction.BLOCK
            block_reason = BlockReason.ML_THREAT_DETECTED
            # Auto-block the IP for CRITICAL threats
            if prediction.risk_level == "CRITICAL":
                await redis_service.block_ip(
                    client_ip,
                    reason=f"ML_CRITICAL:{prediction.threat_type}",
                )
            logger.warning(
                "request_blocked_ml_threat",
                request_id=request_id,
                threat_type=prediction.threat_type,
                risk_level=prediction.risk_level,
                anomaly_score=prediction.anomaly_score,
            )
        elif prediction.is_anomalous:
            # Anomalous but below block threshold → flag for review
            action = GatewayAction.FLAG
            logger.info(
                "request_flagged",
                request_id=request_id,
                threat_type=prediction.threat_type,
                risk_level=prediction.risk_level,
            )

    # ── Step 7: Return ML-blocked requests before proxying ──
    if action == GatewayAction.BLOCK:
        verdict = _build_verdict(
            request_id, client_ip, request.method, request.url.path,
            action, block_reason, prediction, ml_latency_ms,
            (time.perf_counter() - start_time) * 1000,
            request_metadata=metadata,
        )
        await _publish_and_record(verdict)
        detail = "Threat detected and blocked."
        if prediction:
            detail = (
                f"Threat detected: {prediction.threat_type} "
                f"(confidence: {prediction.threat_confidence:.1%}, "
                f"risk: {prediction.risk_level})"
            )
        return _make_block_response(request_id, "threat_detected", detail)

    # ── Step 8: Forward to upstream and incorporate temporal auth signals ──
    upstream_response = await _forward_to_upstream(request, body_bytes, request_id)
    threat_type_override = None
    risk_level_override = None
    is_anomalous_override = None
    if request.method.upper() == "POST" and request.url.path.rstrip("/") == "/api/login":
        if upstream_response.status_code == 401:
            failed_attempts = await redis_service.record_login_result(client_ip, succeeded=False)
            if failed_attempts >= settings.credential_failure_threshold:
                action = GatewayAction.FLAG
                threat_type_override = "CredentialStuffing"
                risk_level_override = "HIGH"
                is_anomalous_override = True
                logger.warning(
                    "credential_stuffing_flagged",
                    request_id=request_id,
                    ip=client_ip,
                    failed_attempts=failed_attempts,
                )
        elif 200 <= upstream_response.status_code < 300:
            await redis_service.record_login_result(client_ip, succeeded=True)

    verdict = _build_verdict(
        request_id, client_ip, request.method, request.url.path,
        action, block_reason, prediction, ml_latency_ms,
        (time.perf_counter() - start_time) * 1000,
        threat_type_override=threat_type_override,
        risk_level_override=risk_level_override,
        is_anomalous_override=is_anomalous_override,
        request_metadata=metadata,
    )
    await _publish_and_record(verdict)
    upstream_response.headers["x-gateway-action"] = action.value
    if threat_type_override is not None:
        upstream_response.headers["x-gateway-threat-type"] = threat_type_override
    return upstream_response


async def _publish_and_record(verdict: GatewayVerdict) -> None:
    """Publish verdict to Kafka and record in metrics."""
    try:
        await kafka_service.publish_verdict(verdict)
    except Exception as exc:
        logger.warning("kafka_verdict_publish_failed", error=str(exc))
    metrics_tracker.record_verdict(verdict)


async def _forward_to_upstream(
    request: Request, body: bytes, request_id: str
) -> Response:
    """
    Forward the request to the upstream e-commerce backend and return the response.
    Acts as a transparent reverse proxy.
    """
    upstream_url = urljoin(
        settings.upstream_base_url,
        request.url.path + ("?" + request.url.query if request.url.query else ""),
    )

    # Build headers, removing hop-by-hop headers
    hop_by_hop = {"host", "transfer-encoding", "connection", "keep-alive"}
    forward_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in hop_by_hop
    }
    forward_headers["x-request-id"] = request_id
    forward_headers["x-forwarded-for"] = _get_client_ip(request)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream_resp = await client.request(
                method=request.method,
                url=upstream_url,
                headers=forward_headers,
                content=body,
            )

        # Build the response, preserving upstream headers
        excluded_headers = {"transfer-encoding", "content-encoding", "content-length"}
        response_headers = {
            k: v
            for k, v in upstream_resp.headers.items()
            if k.lower() not in excluded_headers
        }
        response_headers["x-request-id"] = request_id
        response_headers["x-gateway-action"] = "ALLOW"

        return Response(
            content=upstream_resp.content,
            status_code=upstream_resp.status_code,
            headers=response_headers,
            media_type=upstream_resp.headers.get("content-type"),
        )

    except httpx.TimeoutException:
        logger.error("upstream_timeout", request_id=request_id, url=upstream_url)
        return Response(
            content='{"error": "upstream_timeout", "detail": "The upstream service did not respond in time."}',
            status_code=504,
            media_type="application/json",
        )
    except httpx.ConnectError:
        logger.error("upstream_unreachable", request_id=request_id, url=upstream_url)
        return Response(
            content='{"error": "upstream_unreachable", "detail": "The upstream service is not available."}',
            status_code=502,
            media_type="application/json",
        )
    except Exception as exc:
        logger.error("upstream_error", request_id=request_id, error=str(exc))
        return Response(
            content='{"error": "proxy_error", "detail": "An unexpected error occurred while forwarding the request."}',
            status_code=502,
            media_type="application/json",
        )
