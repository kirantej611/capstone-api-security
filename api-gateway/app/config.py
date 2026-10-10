"""
Configuration module for the API Gateway.

Loads settings from environment variables (with .env fallback) using pydantic-settings.
All service URLs, timeouts, thresholds, and feature flags live here.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Central configuration for the API Gateway.
    Values are loaded from environment variables and/or a .env file.
    """

    # ── Server ──
    gateway_host: str = Field(default="0.0.0.0", description="Host to bind the gateway server")
    gateway_port: int = Field(default=8080, description="Port to bind the gateway server")

    # ── Upstream (Victim E-commerce backend) ──
    upstream_base_url: str = Field(
        default="http://localhost:8081",
        description="Base URL of the upstream e-commerce backend to proxy requests to",
    )

    # ── ML Engine ──
    ml_engine_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the ML inference engine",
    )
    ml_engine_timeout: float = Field(
        default=5.0,
        description="Timeout (seconds) for ML engine inference calls",
    )

    # ── Redis ──
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    blocklist_ttl: int = Field(
        default=3600,
        description="TTL (seconds) for a blocked IP in Redis",
    )
    rate_limit_window: int = Field(
        default=60,
        description="Sliding window size (seconds) for rate limiting",
    )
    rate_limit_max_requests: int = Field(
        default=100,
        description="Max requests allowed per IP within the rate limit window",
    )
    burst_limit_window: int = Field(
        default=10,
        description="Short window size (seconds) for detecting request bursts",
    )
    burst_limit_max_requests: int = Field(
        default=30,
        description="Max requests per IP within the short burst window",
    )
    credential_failure_window: int = Field(
        default=60,
        description="Window size (seconds) for counting failed login attempts",
    )
    credential_failure_threshold: int = Field(
        default=5,
        description="Failed logins from one IP needed to flag credential stuffing",
    )

    # ── Kafka ──
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated Kafka bootstrap servers",
    )
    kafka_topic_requests: str = Field(
        default="api.requests.raw",
        description="Kafka topic to publish raw intercepted request metadata",
    )
    kafka_topic_verdicts: str = Field(
        default="api.verdicts",
        description="Kafka topic to publish ML verdicts and gateway decisions",
    )

    # ── Security Policy ──
    block_on_ml_failure: bool = Field(
        default=False,
        description="If True, block the request when the ML engine is unreachable (fail-closed). "
                    "If False, allow the request through (fail-open).",
    )
    risk_threshold_block: str = Field(
        default="HIGH",
        description="Minimum ML risk_level that triggers an automatic block. "
                    "Options: LOW, MEDIUM, HIGH, CRITICAL",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance – import this throughout the app
settings = Settings()
