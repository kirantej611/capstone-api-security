# Security Backend — Risk Scoring Engine

> Member 3 — Phase 2 | **Language: Go (Gin)** | Port: `8082`

This service is the **security brain** of the system. It:
1. **Consumes** ML predictions from Kafka (`ml-predictions` topic)
2. **Scores** each source IP using a cumulative risk algorithm (stored in Redis)
3. **Blocks** IPs whose risk score exceeds the threshold by adding them to a Redis blocklist
4. **Persists** high-severity alerts to PostgreSQL
5. **Serves** a REST API for the Security Dashboard (Member 4)

---

## Why Go?

| Criteria | Python (FastAPI) | **Go (Gin)** |
|---|---|---|
| Throughput | ~10k req/s | ~100k req/s |
| Memory | ~80MB | ~8MB |
| Startup time | ~1-2s | ~10ms |
| Binary | No (needs interpreter) | **Yes (single static binary)** |
| Docker image size | ~200MB | **~12MB (alpine scratch)** |
| Deploy anywhere | Needs Python runtime | **Single binary — runs anywhere** |

Go is ideal here because this service processes **every single request** that passes through the gateway via Kafka. Low latency and low memory footprint matter a lot.

---

## Architecture

```
Kafka (ml-predictions topic)
        │
        ▼
 kafka/consumer.go
  ├── Parses MLPrediction JSON
  ├── Calculates risk increment from confidence score
  └── Updates Redis risk_score:{ip}
          │
          ▼ (score >= BLOCK_THRESHOLD)
   redis/client.go
    ├── Adds IP to blocklist:{ip}
    └── Saves Alert → PostgreSQL
          │
          ▼
 api/server.go (Gin)
  ├── GET /api/alerts     → recent alerts from Postgres
  ├── GET /api/blocklist  → current blocked IPs from Redis
  └── GET /api/health     → service health
```

---

## Configuration (`.env`)

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8082` | HTTP server port |
| `KAFKA_BROKERS` | `kafka:29092` | Kafka broker addresses |
| `KAFKA_TOPIC` | `ml-predictions` | Topic to consume predictions from |
| `REDIS_ADDR` | `redis:6379` | Redis address |
| `POSTGRES_URL` | `postgres://...` | Postgres connection string |
| `BLOCK_THRESHOLD` | `80.0` | Risk score threshold to block an IP |

---

## Running

### Via Docker Compose (Recommended)
```bash
# From project root
docker compose up -d security-backend
```

### Local Build (requires Go 1.22+)
```bash
cd security-backend
go mod tidy
go run .
```

### Build Binary (deploy anywhere)
```bash
# Linux binary (e.g., for a server)
GOOS=linux GOARCH=amd64 go build -o security-backend-linux .

# Windows binary
GOOS=windows GOARCH=amd64 go build -o security-backend.exe .

# macOS binary
GOOS=darwin GOARCH=arm64 go build -o security-backend-mac .
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/alerts?limit=50` | Recent attack alerts |
| `GET` | `/api/blocklist` | Currently blocked IPs |

---

## File Structure

```
security-backend/
├── main.go                  # Entry point
├── go.mod / go.sum          # Go dependencies
├── Dockerfile               # Multi-stage build (builder + alpine scratch)
├── .env.example
├── config/
│   └── config.go            # Env config loader
├── models/
│   └── models.go            # Shared data structs
├── kafka/
│   └── consumer.go          # Kafka consumer + risk scoring logic
├── redis/
│   └── client.go            # Redis risk score + blocklist operations
├── db/
│   └── postgres.go          # Postgres alerts persistence
└── api/
    └── server.go            # Gin REST API server
```
