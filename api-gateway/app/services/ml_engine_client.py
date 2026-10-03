"""
ML Engine client for the API Gateway.

Makes synchronous (blocking-the-request) calls to the ML inference API to get
real-time threat predictions before forwarding traffic upstream.
"""

import time
from typing import Optional

import httpx

from app.config import settings
from app.logging_config import get_logger
from app.schemas import MLPredictRequest, MLPredictResponse

logger = get_logger("ml_engine_client")


class MLEngineClient:
    """
    Async HTTP client for the ML Engine inference API.

    Wraps the /predict endpoint and provides health checking.
    """

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    # ── Lifecycle ──

    async def connect(self) -> None:
        """Initialize the async HTTP client and verify ML engine is reachable."""
        self._client = httpx.AsyncClient(
            base_url=settings.ml_engine_url,
            timeout=httpx.Timeout(settings.ml_engine_timeout),
        )
        # Check connectivity
        try:
            resp = await self._client.get("/health")
            if resp.status_code == 200:
                self._connected = True
                logger.info("ml_engine_connected", url=settings.ml_engine_url)
            else:
                self._connected = False
                logger.warning(
                    "ml_engine_health_check_failed",
                    status_code=resp.status_code,
                )
        except Exception as exc:
            self._connected = False
            logger.warning(
                "ml_engine_unreachable",
                url=settings.ml_engine_url,
                error=str(exc),
            )

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._connected = False
            logger.info("ml_engine_disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def health_check(self) -> bool:
        """Ping the ML engine /health endpoint."""
        if not self._client:
            return False
        try:
            resp = await self._client.get("/health")
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False

    # ── Prediction ──

    async def predict(
        self,
        url: str,
        method: str,
        body: str = "",
        headers: dict = None,
    ) -> tuple[Optional[MLPredictResponse], float]:
        """
        Call the ML engine's /predict endpoint.

        Args:
            url: The intercepted request URL.
            method: HTTP method (GET, POST, etc.).
            body: Request body string.
            headers: Request headers dict.

        Returns:
            (prediction, latency_ms):
                - prediction: MLPredictResponse if successful, None on failure.
                - latency_ms: Round-trip time in milliseconds.
        """
        if not self._client:
            return None, 0.0

        request_payload = MLPredictRequest(
            url=url,
            method=method,
            body=body,
            headers=headers or {},
        )

        start = time.perf_counter()
        try:
            resp = await self._client.post(
                "/predict",
                json=request_payload.model_dump(),
            )
            latency_ms = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                prediction = MLPredictResponse(**resp.json())
                self._connected = True
                logger.debug(
                    "ml_prediction_received",
                    threat_type=prediction.threat_type,
                    risk_level=prediction.risk_level,
                    latency_ms=round(latency_ms, 2),
                )
                return prediction, latency_ms
            elif resp.status_code == 503:
                logger.warning("ml_engine_models_not_loaded")
                return None, latency_ms
            else:
                logger.warning(
                    "ml_engine_error_response",
                    status_code=resp.status_code,
                    body=resp.text[:200],
                )
                return None, latency_ms

        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.warning("ml_engine_timeout", latency_ms=round(latency_ms, 2))
            return None, latency_ms
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            self._connected = False
            logger.error(
                "ml_engine_request_failed",
                error=str(exc),
                latency_ms=round(latency_ms, 2),
            )
            return None, latency_ms


# Module-level singleton
ml_engine_client = MLEngineClient()
