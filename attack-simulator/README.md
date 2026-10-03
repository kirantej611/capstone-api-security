# Attack Simulator — API Shield Demo Traffic Generator

The Attack Simulator is the **"Attacker"** component of the demo. It generates three types of traffic against the API Gateway, allowing the audience to watch the AI security system detect and block threats in real-time on the Security Dashboard.

## Traffic Types

### 🟢 Normal Traffic (Legitimate Browsing)
Simulates real customers using the e-commerce store:
- Browsing and searching products
- Reading and writing reviews
- Logging in with valid credentials
- Adding items to cart and checking out
- Viewing profile and order history

### 🔴 Attack Traffic (Known Threats)
Fires curated attack payloads at each vulnerable endpoint:

| Attack Type | Target Endpoint | Example Payload |
|-------------|----------------|-----------------|
| SQL Injection | `POST /api/login` | `admin' OR '1'='1` |
| SQL Injection | `GET /api/products/{id}` | `1 UNION SELECT ...` |
| SQL Injection | `GET /api/search?q=` | `' UNION SELECT ...` |
| XSS (Stored) | `POST /api/products/{id}/reviews` | `<script>alert('XSS')</script>` |
| XSS (Reflected) | `GET /api/search?q=` | `<img src=x onerror=alert(1)>` |
| Path Traversal | `GET /api/download?file=` | `../../etc/passwd` |
| Command Injection | `POST /api/ping` | `127.0.0.1; whoami` |

### 🟡 Anomalous Traffic (Suspicious Patterns)
Generates behaviour that triggers the ML anomaly detector:
- **Credential Stuffing** — Rapid-fire login attempts with thousands of username/password combos
- **Rapid Enumeration** — Sequential scanning of product and order IDs
- **Aggressive Scraping** — High-speed product listing with bot user agents

## Demo Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `mixed` | Weighted random mix of all traffic types (default) | General testing |
| `normal` | Normal traffic only | Baseline demo (all green) |
| `attack` | Known attacks only | Showing ML detection |
| `anomalous` | Anomalous traffic only | Showing anomaly detection |
| `demo` | **Scripted 5-phase sequence** | **Business presentations** |

### Demo Mode Phases (Scripted for Presentations)

| Phase | Duration | Traffic | Dashboard Effect |
|-------|----------|---------|-----------------|
| Phase 1 | 20s | Normal browsing | All green, calm |
| Phase 2 | 30s | Known attacks | Alerts fire, red indicators |
| Phase 3 | 20s | Credential stuffing | Rapid anomaly spikes |
| Phase 4 | 20s | Mixed assault | Full attack dashboard |
| Phase 5 | 10s | Normal restored | Returns to green |

## Project Structure

```
attack-simulator/
├── attack_simulator.py      # Main CLI orchestrator with live terminal UI
├── config.py                # Environment variable configuration
├── payloads.py              # Curated attack payload library
├── traffic/
│   ├── __init__.py
│   ├── normal.py            # Legitimate browsing traffic generator
│   ├── attacks.py           # Known attack traffic generator
│   └── anomalous.py         # Anomalous behaviour generator
├── .env.example             # Configuration template
├── Dockerfile               # Container image
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Getting Started

### Prerequisites
- Python 3.11+
- API Gateway running on port 8080
- Victim E-Commerce backend running on port 8081

### Quick Start

```bash
cd attack-simulator
pip install -r requirements.txt

# Run the scripted demo (best for presentations)
python attack_simulator.py --mode demo

# Run mixed traffic for 60 seconds
python attack_simulator.py --mode mixed --duration 60

# Run attacks only, forever (Ctrl+C to stop)
python attack_simulator.py --mode attack --duration 0

# Target a custom gateway URL
python attack_simulator.py --url http://192.168.1.100:8080
```

### Docker

```bash
# Build
docker build -t attack-simulator .

# Run demo sequence (targets gateway container)
docker run --rm --network capstone-api-security_default attack-simulator

# Run mixed traffic for 90 seconds
docker run --rm --network capstone-api-security_default attack-simulator --mode mixed --duration 90
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_URL` | `http://localhost:8080` | Target API Gateway URL |
| `NORMAL_TRAFFIC_DELAY` | `1.0` | Seconds between normal requests |
| `ATTACK_TRAFFIC_DELAY` | `0.5` | Seconds between attack requests |
| `ANOMALOUS_TRAFFIC_DELAY` | `0.05` | Seconds between anomalous requests |
| `NORMAL_TRAFFIC_PCT` | `60` | % normal traffic in mixed mode |
| `ATTACK_TRAFFIC_PCT` | `25` | % attack traffic in mixed mode |
| `ANOMALOUS_TRAFFIC_PCT` | `15` | % anomalous traffic in mixed mode |
| `DEMO_DURATION` | `120` | Default duration (seconds) |
| `CREDENTIAL_STUFFING_BATCH_SIZE` | `50` | Credentials per burst |

## Integration

- **API Gateway** (`api-gateway/`): All traffic targets the gateway on port 8080
- **Victim E-Commerce** (`victim-ecommerce/`): Vulnerable endpoints behind the gateway
- **ML Engine** (`ml-engine/`): Analyses traffic forwarded by the gateway
- **Security Dashboard** (`security-dashboard/`): Shows live blocking activity
