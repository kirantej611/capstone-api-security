"""
In-memory metrics tracker for the API Gateway.

Collects real-time statistics that power the /stats endpoint and the
Security Dashboard's live graphs. Thread-safe via asyncio (single-threaded event loop).
"""

import time
from collections import deque
from typing import Optional

from app.schemas import GatewayAction, GatewayStats, GatewayVerdict, RecentVerdict


class MetricsTracker:
    """
    Lightweight in-memory metrics for the gateway.

    Tracks:
      - Total / allowed / blocked / rate-limited / flagged request counts
      - Rolling ML latency average
      - Recent verdicts ring buffer (for the live dashboard feed)
      - Requests-per-second (1-minute sliding window)
    """

    MAX_RECENT_VERDICTS = 100
    RPS_WINDOW_SECONDS = 60

    def __init__(self) -> None:
        self._start_time = time.time()
        self._total = 0
        self._allowed = 0
        self._blocked = 0
        self._rate_limited = 0
        self._flagged = 0

        # Rolling average for ML latency
        self._ml_latency_sum = 0.0
        self._ml_latency_count = 0

        # Ring buffer of recent verdicts for the dashboard live feed
        self._recent_verdicts: deque[RecentVerdict] = deque(maxlen=self.MAX_RECENT_VERDICTS)

        # Sliding window for RPS calculation (timestamps of recent requests)
        self._request_timestamps: deque[float] = deque()

    def record_verdict(self, verdict: GatewayVerdict) -> None:
        """Record a gateway verdict and update all counters."""
        now = time.time()
        self._total += 1
        self._request_timestamps.append(now)

        # Prune old timestamps outside the window
        cutoff = now - self.RPS_WINDOW_SECONDS
        while self._request_timestamps and self._request_timestamps[0] < cutoff:
            self._request_timestamps.popleft()

        # Update action counters
        if verdict.action == GatewayAction.ALLOW:
            self._allowed += 1
        elif verdict.action == GatewayAction.BLOCK:
            self._blocked += 1
        elif verdict.action == GatewayAction.RATE_LIMIT:
            self._rate_limited += 1
        elif verdict.action == GatewayAction.FLAG:
            self._flagged += 1

        # Track ML latency
        if verdict.ml_latency_ms is not None:
            self._ml_latency_sum += verdict.ml_latency_ms
            self._ml_latency_count += 1

        # Add to recent verdicts
        self._recent_verdicts.append(
            RecentVerdict(
                request_id=verdict.request_id,
                timestamp=verdict.timestamp,
                client_ip=verdict.client_ip,
                method=verdict.method,
                path=verdict.path,
                action=verdict.action,
                threat_type=verdict.threat_type,
                risk_level=verdict.risk_level,
                anomaly_score=verdict.anomaly_score,
                is_anomalous=verdict.is_anomalous,
                block_reason=verdict.block_reason,
                threat_confidence=verdict.threat_confidence,
                all_probabilities=verdict.all_probabilities,
                feature_importance=verdict.feature_importance,
                headers=verdict.headers,
                body=verdict.body,
                query_params=verdict.query_params,
                ml_latency_ms=verdict.ml_latency_ms,
                total_latency_ms=verdict.total_latency_ms,
            )
        )

    def get_stats(self, active_blocked_ips: int = 0) -> GatewayStats:
        """Return current gateway statistics snapshot."""
        now = time.time()
        uptime = now - self._start_time

        # Prune old timestamps
        cutoff = now - self.RPS_WINDOW_SECONDS
        while self._request_timestamps and self._request_timestamps[0] < cutoff:
            self._request_timestamps.popleft()

        rps = len(self._request_timestamps) / self.RPS_WINDOW_SECONDS if self._request_timestamps else 0.0
        avg_ml = (self._ml_latency_sum / self._ml_latency_count) if self._ml_latency_count > 0 else 0.0

        return GatewayStats(
            total_requests=self._total,
            allowed_requests=self._allowed,
            blocked_requests=self._blocked,
            rate_limited_requests=self._rate_limited,
            flagged_requests=self._flagged,
            avg_ml_latency_ms=round(avg_ml, 2),
            active_blocked_ips=active_blocked_ips,
            uptime_seconds=round(uptime, 1),
            requests_per_second=round(rps, 2),
        )

    def get_recent_verdicts(self, limit: int = 50) -> list[RecentVerdict]:
        """Return the most recent verdicts (newest first)."""
        verdicts = list(self._recent_verdicts)
        verdicts.reverse()
        return verdicts[:limit]


# Module-level singleton
metrics_tracker = MetricsTracker()
