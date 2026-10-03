# API Gateway — AI-Powered Security Shield

The API Gateway is the **front-line defense** of the API Shield system. It sits in front of the victim e-commerce application, intercepting all incoming HTTP traffic, analyzing it through ML models in real-time, and blocking threats before they reach the backend.

## Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────────────────┐     ┌───────────────────┐
│   Clients /  │     │                    API GATEWAY (:8080)                  │     │  Victim E-Commerce│
│   Attackers  │────▶│  ┌───────────┐  ┌──────────┐  ┌────────────────────┐   │────▶│   Backend (:8081) │
│              │     │  │ Blocklist │  │ Rate     │  │  ML Engine Client  │   │     │                   │
│              │     │  │ Check     │  │ Limiter  │  │  (Threat Analysis) │   │     │                   │
│              │     │  └─────┬─────┘  └────┬─────┘  └─────────┬──────────┘   │     └───────────────────┘
│              │     │        │              │                  │              │
│              │     │        ▼              ▼                  ▼              │
│              │     │  ┌─────────────────────────────────────────────┐        │
│              │     │  │          Kafka Event Publisher              │        │
│              │     │  │  (api.requests.raw  &  api.verdicts)       │        │
│              │     │  └────────────────────────────────────────────-┘        │
│              │     └─────────────────────────────────────────────────────────┘
│              │                              │
│              │                              ▼
│              │                    ┌───────────────────┐
│              │                    │ Security Backend   │
│              │                    │ (Risk Scorer +     │
│              │                    │  Dashboard API)    │
│              │                    └───────────────────┘
```

## Request Processing Pipeline

Every request flows through this pipeline:

1. **Correlation ID** — Unique `X-Request-ID` assigned to every request
2. **Redis Blocklist Check** — Immediately block known bad IPs
3. **Rate Limiting** — Sliding-window counter per IP (auto-blocks at 3x threshold)
4. **ML Threat Analysis** — Call the ML Engine's `/predict` endpoint for real-time threat detection
5. **Security Policy** — Block if risk ≥ configured threshold (default: HIGH); auto-block CRITICAL IPs
6. **Kafka Publishing** — Publish request metadata + verdict for async processing
7. **Reverse Proxy** — Forward allowed requests to the upstream e-commerce backend

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Server | FastAPI + Uvicorn |
| Reverse Proxy | httpx (async) |
| Blocklist & Rate Limiting | Redis |
| Event Streaming | Apache Kafka (aiokafka) |
| ML Integration | httpx → ML Engine `/predict` |
| Logging | structlog (JSON) |
| Configuration | pydantic-settings + `.env` |
| Testing | pytest + FastAPI TestClient |
| Containerization | Docker |

## Project Structure

```
api-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifecycle, admin endpoints
│   ├── config.py            # Environment variable configuration
│   ├── schemas.py           # Pydantic data models & Kafka event schemas
│   ├── proxy_handler.py     # Core request pipeline (blocklist → ML → proxy)
│   ├── middleware.py         # Correlation ID & timing middleware
│   ├── metrics.py           # In-memory metrics tracker
│   ├── logging_config.py    # Structured JSON logging setup
│   └── services/
│       ├── __init__.py
│       ├── redis_service.py      # Redis blocklist & rate limiter
│       ├── kafka_service.py      # Kafka event producer
│       └── ml_engine_client.py   # ML Engine HTTP client
├── tests/
│   ├── __init__.py
│   └── test_gateway.py     # Unit & integration tests
├── .env.example             # Environment variable template
├── Dockerfile               # Production container image
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for Redis, Kafka, PostgreSQL)

### Local Development

1. **Start infrastructure:**
   ```bash
   docker-compose up -d  # from project root
   ```

2. **Install dependencies:**
   ```bash
   cd api-gateway
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

4. **Run the gateway:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

5. **Run tests:**
   ```bash
   pip install pytest
   pytest tests/ -v
   ```

### Docker

```bash
docker build -t api-gateway .
docker run -p 8080:8080 --env-file .env api-gateway
```

## API Endpoints

### Admin Endpoints (`/gateway/*`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/gateway/health` | Health check with service connectivity |
| `GET` | `/gateway/stats` | Real-time gateway statistics |
| `GET` | `/gateway/verdicts/recent` | Recent verdicts for dashboard live feed |
| `GET` | `/gateway/blocklist` | List all blocked IPs |
| `POST` | `/gateway/blocklist/{ip}` | Add IP to blocklist |
| `DELETE` | `/gateway/blocklist/{ip}` | Remove IP from blocklist |

### Proxy Route

All other routes (`/*`) are intercepted, analyzed, and proxied to the upstream e-commerce backend.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_HOST` | `0.0.0.0` | Server bind host |
| `GATEWAY_PORT` | `8080` | Server bind port |
| `UPSTREAM_BASE_URL` | `http://localhost:8081` | E-commerce backend URL |
| `ML_ENGINE_URL` | `http://localhost:8000` | ML inference engine URL |
| `ML_ENGINE_TIMEOUT` | `5.0` | ML call timeout (seconds) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `BLOCKLIST_TTL` | `3600` | Blocked IP TTL (seconds) |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |
| `RATE_LIMIT_MAX_REQUESTS` | `100` | Max requests per window |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `KAFKA_TOPIC_REQUESTS` | `api.requests.raw` | Raw request metadata topic |
| `KAFKA_TOPIC_VERDICTS` | `api.verdicts` | Gateway verdict topic |
| `BLOCK_ON_ML_FAILURE` | `false` | Fail-closed when ML unavailable |
| `RISK_THRESHOLD_BLOCK` | `HIGH` | Min risk level to auto-block |

## Integration with Other Services

- **ML Engine** (`ml-engine/`): Called synchronously via `/predict` for real-time threat detection
- **Security Backend** (`security-backend/`): Consumes Kafka topics for persistence, risk scoring, and dashboard data
- **Security Dashboard** (`security-dashboard/`): Polls `/gateway/stats` and `/gateway/verdicts/recent` for live visualization
- **Victim E-Commerce** (`victim-ecommerce/`): Upstream target proxied through the gateway
- **Attack Simulator** (`attack-simulator/`): Generates traffic targeting the gateway for demo purposes
