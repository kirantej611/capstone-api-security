# Victim E-Commerce Backend API

> ⚠️ **WARNING**: This application is **intentionally vulnerable** and designed for security demonstration purposes only. Do NOT deploy in production.

A simple e-commerce backend API built with FastAPI that serves as the "victim" application in the Deep Learning-Driven API Attack Detection System demo. The API Gateway (Member 2) sits in front of this service, intercepting traffic for ML analysis.

## Tech Stack

- **Framework**: Python 3.11 + FastAPI
- **Database**: PostgreSQL (separate `victim_ecommerce_db`)
- **Auth**: JWT (intentionally weak)
- **ORM**: Raw SQL via `asyncpg` (intentionally vulnerable)

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL running (via `docker-compose up -d postgres` from project root)

### Local Development
```bash
cd victim-ecommerce
pip install -r requirements.txt
cp .env.example .env  # Edit if needed
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Docker
```bash
docker build -t victim-ecommerce .
docker run -p 8080:8080 --env-file .env victim-ecommerce
```

## API Endpoints

| Method | Endpoint | Description | Vulnerability |
|--------|----------|-------------|---------------|
| `POST` | `/api/login` | User login | **SQL Injection** |
| `POST` | `/api/auth/register` | Register user | None |
| `GET` | `/api/products` | List products | None |
| `GET` | `/api/products/{id}` | Product details | **SQL Injection** |
| `GET` | `/api/search?q=` | Search products | **SQLi + Reflected XSS** |
| `POST` | `/api/products/{id}/reviews` | Add review | **Stored XSS** |
| `GET` | `/api/products/{id}/reviews` | Get reviews | Reflects XSS |
| `POST` | `/api/cart/add` | Add to cart | **BOLA** |
| `GET` | `/api/cart` | View cart | **BOLA** |
| `POST` | `/api/checkout` | Checkout | No rate limit |
| `GET` | `/api/orders/{id}` | View order | **BOLA** |
| `GET` | `/api/user/profile` | User profile | **BOLA** |
| `GET` | `/api/download?file=` | Download file | **Path Traversal** |
| `POST` | `/api/ping` | Ping host | **Command Injection** |
| `GET` | `/api/health` | Health check | None |

## Vulnerability Mode

Set `VULN_MODE=true` (default) to enable intentional vulnerabilities. Set `VULN_MODE=false` for safe mode with parameterized queries and input sanitization.

## Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |
| user1 | password123 | customer |
| user2 | password456 | customer |

## Testing

```bash
# Start the app first, then run tests
pytest tests/test_endpoints.py -v
```

## Integration

This service is designed to run behind the API Gateway (port 8000). The gateway proxies requests to `http://victim-ecommerce:8080` and streams request metadata to Kafka for ML analysis.
