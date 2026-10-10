"""
Redis service for the API Gateway.

Handles:
  - IP blocklist management (add / check / remove / list)
  - Rate limiting via sliding-window counters
  - Connection lifecycle (connect / disconnect / health)
"""

import time
from typing import List, Optional

import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("redis_service")


class RedisService:
    """Async Redis client wrapping blocklist and rate-limiting operations."""

    BLOCKLIST_PREFIX = "blocklist:ip:"
    RATE_LIMIT_PREFIX = "ratelimit:ip:"
    BURST_LIMIT_PREFIX = "burstlimit:ip:"
    LOGIN_FAILURE_PREFIX = "loginfail:ip:"

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None
        self._connected = False

    # ── Lifecycle ──

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def connect(self) -> None:
        """Establish the Redis connection with retry logic."""
        try:
            self._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._client.ping()
            self._connected = True
            logger.info("redis_connected", url=settings.redis_url)
        except Exception as exc:
            self._connected = False
            logger.error("redis_connection_failed", error=str(exc))
            raise

    async def disconnect(self) -> None:
        """Gracefully close the Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("redis_disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def health_check(self) -> bool:
        """Return True if Redis responds to PING."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            self._connected = False
            return False

    # ── Blocklist ──

    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is on the blocklist."""
        if not self._client:
            return False
        try:
            result = await self._client.exists(f"{self.BLOCKLIST_PREFIX}{ip}")
            return bool(result)
        except Exception as exc:
            logger.warning("redis_blocklist_check_failed", ip=ip, error=str(exc))
            return False

    async def block_ip(self, ip: str, reason: str = "", ttl: Optional[int] = None) -> None:
        """
        Add an IP to the blocklist with a TTL.

        Args:
            ip: The IP address to block.
            reason: Human-readable reason for the block.
            ttl: Override default TTL (seconds). None uses config default.
        """
        if not self._client:
            return
        key = f"{self.BLOCKLIST_PREFIX}{ip}"
        ttl = ttl or settings.blocklist_ttl
        try:
            await self._client.setex(key, ttl, reason or "blocked_by_gateway")
            logger.info("ip_blocked", ip=ip, reason=reason, ttl=ttl)
        except Exception as exc:
            logger.error("redis_block_ip_failed", ip=ip, error=str(exc))

    async def unblock_ip(self, ip: str) -> bool:
        """Remove an IP from the blocklist. Returns True if it was present."""
        if not self._client:
            return False
        try:
            result = await self._client.delete(f"{self.BLOCKLIST_PREFIX}{ip}")
            if result:
                logger.info("ip_unblocked", ip=ip)
            return bool(result)
        except Exception as exc:
            logger.error("redis_unblock_ip_failed", ip=ip, error=str(exc))
            return False

    async def get_blocklist_entries(self) -> List[dict[str, str]]:
        """Return blocklisted IPs together with their stored block reasons."""
        if not self._client:
            return []
        try:
            entries = []
            async for key in self._client.scan_iter(f"{self.BLOCKLIST_PREFIX}*"):
                ip = key.removeprefix(self.BLOCKLIST_PREFIX)
                reason = await self._client.get(key)
                entries.append({"ip": ip, "reason": reason or "blocked_by_gateway"})
            return entries
        except Exception as exc:
            logger.error("redis_list_blocked_failed", error=str(exc))
            return []

    async def get_blocked_ips(self) -> List[str]:
        """Return all currently blocked IPs."""
        entries = await self.get_blocklist_entries()
        return [entry["ip"] for entry in entries]

    async def get_blocked_ip_count(self) -> int:
        """Return count of currently blocked IPs (for dashboard stats)."""
        ips = await self.get_blocked_ips()
        return len(ips)

    # ── Rate Limiting (Sliding Window Counter) ──

    async def check_rate_limit(self, ip: str) -> tuple[bool, int]:
        """
        Check if the IP has exceeded the rate limit.

        Uses a sliding-window counter pattern:
          - Key: ratelimit:ip:<ip>
          - INCR the key; on first creation, set EXPIRE to window size.

        Returns:
            (is_allowed, current_count)
        """
        if not self._client:
            return True, 0  # fail-open if Redis is down

        key = f"{self.RATE_LIMIT_PREFIX}{ip}"
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = await pipe.execute()

            current_count = results[0]
            ttl = results[1]

            # If the key is new (ttl == -1), set the expiry window
            if ttl == -1:
                await self._client.expire(key, settings.rate_limit_window)

            is_allowed = current_count <= settings.rate_limit_max_requests
            return is_allowed, current_count

        except Exception as exc:
            logger.warning("redis_rate_limit_check_failed", ip=ip, error=str(exc))
            return True, 0  # fail-open

    async def check_burst_limit(self, ip: str) -> tuple[bool, int]:
        """Count requests in a short window to identify sudden bursts."""
        if not self._client:
            return True, 0

        key = f"{self.BURST_LIMIT_PREFIX}{ip}"
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, settings.burst_limit_window)
                results = await pipe.execute()
            current_count = results[0]
            return current_count <= settings.burst_limit_max_requests, current_count
        except Exception as exc:
            logger.warning("redis_burst_limit_check_failed", ip=ip, error=str(exc))
            return True, 0

    async def record_login_result(self, ip: str, succeeded: bool) -> int:
        """Track failed login responses per IP and clear the count after a success."""
        if not self._client:
            return 0

        key = f"{self.LOGIN_FAILURE_PREFIX}{ip}"
        try:
            if succeeded:
                await self._client.delete(key)
                return 0

            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, settings.credential_failure_window)
                results = await pipe.execute()
            return results[0]
        except Exception as exc:
            logger.warning("redis_login_failure_tracking_failed", ip=ip, error=str(exc))
            return 0


# Module-level singleton
redis_service = RedisService()
