"""
API Gateway — Main FastAPI Application

This is the entry point for the API Gateway service. It orchestrates:
  - Service lifecycle (Redis, Kafka, ML Engine connections)
  - Middleware registration (CORS, correlation IDs, timing)
  - Admin endpoints (health, stats, recent verdicts, blocklist management)
  - Catch-all proxy route (all other traffic → proxy_handler)
"""

import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import get_logger, setup_logging
from app.metrics import metrics_tracker
from app.middleware import CorrelationIDMiddleware, TimingMiddleware
from app.proxy_handler import handle_request
from app.schemas import GatewayStats, HealthResponse, RecentVerdict
from app.services.kafka_service import kafka_service
from app.services.ml_engine_client import ml_engine_client
from app.services.redis_service import redis_service

# Setup structured logging
setup_logging()
logger = get_logger("main")

_start_time = time.time()


# ── Application Lifecycle ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage startup and shutdown of all external service connections.
    """
    logger.info("gateway_starting", port=settings.gateway_port)

    # Connect to services (each has its own retry logic)
    try:
        await redis_service.connect()
    except Exception as exc:
        logger.error("redis_startup_failed", error=str(exc))

    try:
        await kafka_service.connect()
    except Exception as exc:
        logger.error("kafka_startup_failed", error=str(exc))

    try:
        await ml_engine_client.connect()
    except Exception as exc:
        logger.warning("ml_engine_startup_failed", error=str(exc))

    logger.info(
        "gateway_started",
        redis=redis_service.is_connected,
        kafka=kafka_service.is_connected,
        ml_engine=ml_engine_client.is_connected,
    )

    yield  # ← Application is running

    # Shutdown
    logger.info("gateway_shutting_down")
    await ml_engine_client.disconnect()
    await kafka_service.disconnect()
    await redis_service.disconnect()
    logger.info("gateway_stopped")


# ── FastAPI App ──

app = FastAPI(
    title="API Shield Gateway",
    description=(
        "AI-powered API Gateway that intercepts traffic, runs ML-based threat detection, "
        "and blocks malicious requests in real-time."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (order matters: outermost first) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimingMiddleware)
app.add_middleware(CorrelationIDMiddleware)


# ══════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS  (prefixed with /gateway/ to avoid collisions
#                   with proxied e-commerce routes)
# ══════════════════════════════════════════════════════════════


@app.get("/gateway/health", response_model=HealthResponse, tags=["Admin"])
async def health_check():
    """
    Health check endpoint.
    Returns connectivity status for Redis, Kafka, and the ML Engine.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="api-gateway",
        redis_connected=await redis_service.health_check(),
        kafka_connected=await kafka_service.health_check(),
        ml_engine_connected=await ml_engine_client.health_check(),
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.get("/gateway/stats", response_model=GatewayStats, tags=["Dashboard"])
async def get_stats():
    """
    Real-time gateway statistics for the Security Dashboard.
    Includes request counts, ML latency, RPS, and blocked IP count.
    """
    blocked_count = await redis_service.get_blocked_ip_count()
    return metrics_tracker.get_stats(active_blocked_ips=blocked_count)


@app.get("/gateway/verdicts/recent", response_model=List[RecentVerdict], tags=["Dashboard"])
async def get_recent_verdicts(limit: int = 50):
    """
    Returns the most recent gateway verdicts for the dashboard live feed.
    """
    return metrics_tracker.get_recent_verdicts(limit=min(limit, 100))


@app.get("/gateway/blocklist", tags=["Admin"])
async def get_blocklist():
    """
    List all currently blocked IPs.
    """
    entries = await redis_service.get_blocklist_entries()
    return {
        "blocked_ips": [entry["ip"] for entry in entries],
        "entries": entries,
        "count": len(entries),
    }


@app.post("/gateway/blocklist/{ip}", tags=["Admin"])
async def add_to_blocklist(ip: str, reason: str = "manual_block", ttl: int = None):
    """
    Manually add an IP to the blocklist.
    """
    await redis_service.block_ip(ip, reason=reason, ttl=ttl)
    return {"status": "blocked", "ip": ip, "reason": reason}


@app.delete("/gateway/blocklist/{ip}", tags=["Admin"])
async def remove_from_blocklist(ip: str):
    """
    Remove an IP from the blocklist.
    """
    removed = await redis_service.unblock_ip(ip)
    return {"status": "unblocked" if removed else "not_found", "ip": ip}


# ══════════════════════════════════════════════════════════════
# CATCH-ALL PROXY ROUTE
# Any request that doesn't match /gateway/* is proxied through
# the ML analysis pipeline to the upstream e-commerce backend.
# ══════════════════════════════════════════════════════════════


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    tags=["Proxy"],
    include_in_schema=False,
)
async def proxy_catchall(request: Request):
    """
    Catch-all route: every request that isn't a gateway admin endpoint
    is intercepted, analyzed by ML, and proxied to the upstream service.
    """
    return await handle_request(request)
