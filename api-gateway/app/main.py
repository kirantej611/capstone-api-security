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


import os
import time
import re
import httpx
import asyncio
import google.generativeai as genai
from fastapi import Request, HTTPException

# Initialize Gemini Client (expects GEMINI_API_KEY environment variable)
api_key = os.environ.get("GEMINI_API_KEY", "dummy-key-if-not-set")
if api_key != "dummy-key-if-not-set":
    genai.configure(api_key=api_key)

SYSTEM_PROMPT = """You are Alex, a friendly, approachable security copilot on the AEGIS-AI team.
Your job is to explain security events, system health, and threat findings in clear, human, conversational language—like a helpful teammate chatting on Slack.

COMMUNICATION STYLE:
- Talk in warm, natural, human sentences.
- NEVER dump raw technical log lines, bullet points, or say "according to the telemetry".
- Explain security concepts (like BOLA, SQL injection, or brute force) in simple, accessible terms.
- If everything is quiet and calm, be reassuring and positive.
- Keep responses concise: 2 to 4 sentences maximum."""

class ChatbotRouter:
    """Production-grade conversational intent router for the SecOps Assistant with human-friendly context."""
    def __init__(self):
        self.routes = [
            (re.compile(r'^\b(firewall|block|blocked|list)\b$', re.IGNORECASE), self._handle_firewall),
            (re.compile(r'^\b(status|health|uptime|systems)\b$', re.IGNORECASE), self._handle_status),
            (re.compile(r'^\b(attack|threat|recent|logs)\b$', re.IGNORECASE), self._handle_threats),
        ]
        self.rate_limits = {}  # Format: {ip: [timestamps]}
        self.MAX_REQS_PER_MIN = 20

    def _check_rate_limit(self, client_ip: str) -> bool:
        now = time.time()
        self.rate_limits[client_ip] = [ts for ts in self.rate_limits.get(client_ip, []) if now - ts < 60]
        if len(self.rate_limits[client_ip]) >= self.MAX_REQS_PER_MIN:
            return False
        self.rate_limits[client_ip].append(now)
        return True

    async def get_live_cluster_data(self) -> dict:
        """Collect live cluster statistics and threat intelligence in a structured dictionary."""
        uptime_min = round((time.time() - _start_time) / 60, 1)
        total_reqs = 0
        allowed_reqs = 0
        blocked_reqs = 0
        ml_latency = 0.0

        try:
            blocked_count = await redis_service.get_blocked_ip_count()
            stats = metrics_tracker.get_stats(active_blocked_ips=blocked_count)
            total_reqs = stats.total_requests
            allowed_reqs = stats.allowed_requests
            blocked_reqs = stats.blocked_requests
            ml_latency = round(stats.avg_ml_latency_ms, 1)
        except Exception:
            pass

        blocked_ips = []
        try:
            entries = await redis_service.get_blocklist_entries()
            for e in entries[:5]:
                reason = e.get("reason", "suspicious behavior")
                blocked_ips.append(f"{e.get('ip')} (flagged for {reason})")
        except Exception:
            pass

        recent_threats = []
        try:
            verdicts = metrics_tracker.get_recent_verdicts(limit=25)
            threat_verdicts = [v for v in verdicts if v.action in ("BLOCK", "RATE_LIMIT", "FLAG")]
            for v in threat_verdicts[-3:]:
                recent_threats.append(
                    f"{v.threat_type} attack attempt on {v.method} {v.path} from {v.client_ip}"
                )
        except Exception:
            pass

        return {
            "uptime_min": uptime_min,
            "total_reqs": total_reqs,
            "allowed_reqs": allowed_reqs,
            "blocked_reqs": blocked_reqs,
            "ml_latency": ml_latency,
            "blocked_ips": blocked_ips,
            "recent_threats": recent_threats,
        }

    async def _handle_firewall(self, msg: str) -> str:
        data = await self.get_live_cluster_data()
        blocked = data["blocked_ips"]
        if blocked:
            return (
                f"🛡️ The firewall is actively guarding the cluster! Right now, we have {len(blocked)} blocked source: "
                f"{', '.join(blocked)}. The gateway is automatically filtering them out so your services stay safe."
            )
        return "🛡️ The firewall is up and running smoothly! No IPs are currently blocked, and all incoming traffic has passed our security checks."

    async def _handle_status(self, msg: str) -> str:
        data = await self.get_live_cluster_data()
        return (
            f"✅ Everything is running in top shape! We've been up for about {data['uptime_min']} minutes and processed "
            f"{data['total_reqs']} requests so far ({data['blocked_reqs']} blocked as threats). "
            f"Our AI models are scanning requests in a snappy {data['ml_latency']}ms on average."
        )

    async def _handle_threats(self, msg: str) -> str:
        data = await self.get_live_cluster_data()
        threats = data["recent_threats"]
        if threats:
            return (
                f"⚠️ Here's the latest threat we neutralized: {threats[-1]}. "
                "Our ML firewall intercepted it immediately before it could touch any sensitive customer data."
            )
        return "✨ All quiet on the threat radar! We haven't observed any suspicious attacks recently, and all recent requests look completely harmless."

    async def route(self, msg: str, client_ip: str) -> str:
        # 1. Rate Limiting Check
        if not self._check_rate_limit(client_ip):
            return "Whoa there, give me just a few seconds! I'm catching my breath before answering more questions."

        # 2. Check explicit quick action keywords
        for pattern, handler in self.routes:
            if pattern.search(msg):
                return await handler(msg)

        # 3. Retrieve live cluster data
        data = await self.get_live_cluster_data()

        # Build a human-friendly briefing for the LLM
        briefing = (
            f"CURRENT SITUATION BRIEFING:\n"
            f"- Traffic volume: {data['total_reqs']} requests total ({data['allowed_reqs']} normal, {data['blocked_reqs']} stopped)\n"
            f"- ML inspection speed: {data['ml_latency']}ms average latency\n"
            f"- Blocklist: {', '.join(data['blocked_ips']) if data['blocked_ips'] else 'None currently blocked'}\n"
            f"- Recent incidents: {', '.join(data['recent_threats']) if data['recent_threats'] else 'No recent attacks detected'}\n"
            f"- System uptime: {data['uptime_min']} minutes, all services healthy."
        )

        augmented_system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"CRITICAL INSTRUCTION: You MUST base your answer strictly on the following CURRENT SITUATION BRIEFING. "
            f"Do not hallucinate attacks, IPs, or stats that are not in this briefing. "
            f"If the briefing says 'No recent attacks detected', you must say that everything is safe.\n\n"
            f"{briefing}"
        )

        # 4. Query Groq API
        try:
            groq_api_key = os.environ.get("GROQ_API_KEY", "")
            if not groq_api_key:
                for env_file in [".env", "../.env", "/app/.env"]:
                    if os.path.exists(env_file):
                        try:
                            with open(env_file, "r") as ef:
                                for line in ef:
                                    if line.startswith("GROQ_API_KEY="):
                                        groq_api_key = line.strip().split("=", 1)[1].strip("'\" ")
                                        break
                        except Exception:
                            pass
                    if groq_api_key:
                        break

            if not groq_api_key:
                return self._simulate_llm_response(msg, data)

            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_api_key}"},
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [
                            {"role": "system", "content": augmented_system_prompt},
                            {"role": "user", "content": msg}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 150
                    },
                    timeout=20.0
                )
                
            if res.status_code == 200:
                content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                content = content.strip('"\' ')
                
                # Guard against false lack-of-access hallucinations from small models
                refusal_phrases = ["don't have access", "not have access", "not provided", "i am not able to see", "unable to provide"]
                if any(phrase in content.lower() for phrase in refusal_phrases):
                    logger.warning("llm_refusal_detected", content=content)
                    return self._simulate_llm_response(msg, data)

                if content and not content.startswith("- ") and not content.startswith("==="):
                    return content
                return self._simulate_llm_response(msg, data)
            else:
                logger.error("groq_api_error", status_code=res.status_code, response=res.text)
                return self._simulate_llm_response(msg, data)
                
        except Exception as e:
            logger.error("llm_exception", error=str(e))
            return self._simulate_llm_response(msg, data)
            
    def _simulate_llm_response(self, msg: str, data: dict) -> str:
        msg_lower = msg.lower()
        blocked = data.get("blocked_ips", [])
        total = data.get("total_reqs", 0)
        blocked_count = data.get("blocked_reqs", 0)
        threats = data.get("recent_threats", [])
        
        if "ip" in msg_lower or "block" in msg_lower:
            if blocked:
                return (
                    f"Right now, we have {len(blocked)} IP on our blocklist: {', '.join(blocked)}. "
                    "Our firewall automatically caught and isolated it to keep the API safe."
                )
            return "Good news! There aren't any IPs blocked right now. All recent traffic looks safe and normal."

        elif "attack" in msg_lower or "threat" in msg_lower or "incident" in msg_lower:
            if threats:
                return (
                    f"Our ML firewall recently stopped {len(threats)} potential attack attempt(s), including {threats[-1]}. "
                    "Everything was mitigated before reaching downstream services."
                )
            return "Things are very calm right now! We haven't detected any active attacks, and all incoming requests have passed our ML safety checks."

        elif "status" in msg_lower or "health" in msg_lower or "how" in msg_lower or "cluster" in msg_lower or "metric" in msg_lower:
            return (
                f"All systems are running smoothly! We've processed {total} requests so far (blocking {blocked_count} suspicious ones), "
                f"and our ML models are scanning payloads in just {data.get('ml_latency', 0)}ms. Everything is fully operational."
            )

        elif "architecture" in msg_lower or "platform" in msg_lower or "work" in msg_lower:
            return (
                "AEGIS-AI works like an intelligent shield in front of your web APIs. When requests arrive, our gateway runs them "
                "through an ML ensemble (Isolation Forest and attack classifiers) in under 15ms. If it spots malicious patterns like "
                "BOLA or SQL injections, it blocks the IP in Redis and alerts the dashboard instantly."
            )

        elif "who" in msg_lower or "what" in msg_lower:
            return (
                "Hey! I'm Alex, your SecOps copilot here at AEGIS-AI. I keep an eye on incoming traffic, track anomalies, and help "
                "you stay on top of any threats targeting our APIs."
            )

        else:
            return (
                f"I'm keeping a close eye on the gateway! Right now we've handled {total} requests and everything is looking solid. "
                "Feel free to ask about any blocked IPs, recent attacks, or how our detection models work!"
            )

chatbot_router = ChatbotRouter()

@app.post("/gateway/chat", tags=["Dashboard"])
async def chatbot_respond(request: Request, payload: dict):
    """
    Chatbot backend integration for the SecOps Assistant.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_msg = payload.get("message", "")
    response_text = await chatbot_router.route(user_msg, client_ip)
    return {"reply": response_text}


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
