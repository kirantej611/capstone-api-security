"""
Kafka producer service for the API Gateway.

Publishes two types of events:
  1. RequestMetadata → `api.requests.raw` topic (raw intercepted request data)
  2. GatewayVerdict  → `api.verdicts` topic (final gateway decision + ML results)

The Security Backend consumes these for persistence, risk scoring, and the dashboard.
"""

import json
from typing import Optional

from aiokafka import AIOKafkaProducer
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logging_config import get_logger
from app.schemas import RequestMetadata, GatewayVerdict

logger = get_logger("kafka_service")


class KafkaService:
    """Async Kafka producer for publishing gateway events."""

    def __init__(self) -> None:
        self._producer: Optional[AIOKafkaProducer] = None
        self._connected = False

    # ── Lifecycle ──

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def connect(self) -> None:
        """Start the Kafka producer with retry logic."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                request_timeout_ms=10000,
                retry_backoff_ms=500,
            )
            await self._producer.start()
            self._connected = True
            logger.info("kafka_connected", servers=settings.kafka_bootstrap_servers)
        except Exception as exc:
            self._connected = False
            logger.error("kafka_connection_failed", error=str(exc))
            raise

    async def disconnect(self) -> None:
        """Gracefully flush and stop the Kafka producer."""
        if self._producer:
            try:
                await self._producer.stop()
            except Exception as exc:
                logger.warning("kafka_disconnect_error", error=str(exc))
            self._connected = False
            logger.info("kafka_disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def health_check(self) -> bool:
        """Return True if the producer is running."""
        return self._connected and self._producer is not None

    # ── Publishing ──

    async def publish_request_metadata(self, metadata: RequestMetadata) -> None:
        """
        Publish raw request metadata to the requests topic.

        Key: client_ip (for partitioning — same IP always goes to same partition).
        """
        if not self._producer or not self._connected:
            logger.warning("kafka_publish_skipped", reason="not_connected", topic="requests")
            return
        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_requests,
                key=metadata.client_ip,
                value=metadata.model_dump(),
            )
            logger.debug(
                "kafka_request_published",
                request_id=metadata.request_id,
                topic=settings.kafka_topic_requests,
            )
        except Exception as exc:
            logger.error(
                "kafka_publish_failed",
                topic=settings.kafka_topic_requests,
                request_id=metadata.request_id,
                error=str(exc),
            )

    async def publish_verdict(self, verdict: GatewayVerdict) -> None:
        """
        Publish the gateway's final verdict to the verdicts topic.

        Key: client_ip (for partitioning).
        """
        if not self._producer or not self._connected:
            logger.warning("kafka_publish_skipped", reason="not_connected", topic="verdicts")
            return
        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_verdicts,
                key=verdict.client_ip,
                value=verdict.model_dump(),
            )
            logger.debug(
                "kafka_verdict_published",
                request_id=verdict.request_id,
                action=verdict.action,
                topic=settings.kafka_topic_verdicts,
            )
        except Exception as exc:
            logger.error(
                "kafka_publish_failed",
                topic=settings.kafka_topic_verdicts,
                request_id=verdict.request_id,
                error=str(exc),
            )


# Module-level singleton
kafka_service = KafkaService()
