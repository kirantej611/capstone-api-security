"""
Configuration for the Attack Simulator.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Target — always the API Gateway, NOT the e-commerce backend directly
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")

# ── Speed controls (seconds between requests) ──
NORMAL_TRAFFIC_DELAY = float(os.getenv("NORMAL_TRAFFIC_DELAY", "1.0"))
ATTACK_TRAFFIC_DELAY = float(os.getenv("ATTACK_TRAFFIC_DELAY", "0.5"))
ANOMALOUS_TRAFFIC_DELAY = float(os.getenv("ANOMALOUS_TRAFFIC_DELAY", "0.05"))

# ── Traffic mix (must sum to 100) ──
NORMAL_TRAFFIC_PCT = int(os.getenv("NORMAL_TRAFFIC_PCT", "60"))
ATTACK_TRAFFIC_PCT = int(os.getenv("ATTACK_TRAFFIC_PCT", "25"))
ANOMALOUS_TRAFFIC_PCT = int(os.getenv("ANOMALOUS_TRAFFIC_PCT", "15"))

# ── Demo duration ──
DEMO_DURATION = int(os.getenv("DEMO_DURATION", "120"))  # 0 = forever

# ── Credential stuffing ──
CREDENTIAL_STUFFING_BATCH_SIZE = int(os.getenv("CREDENTIAL_STUFFING_BATCH_SIZE", "50"))
