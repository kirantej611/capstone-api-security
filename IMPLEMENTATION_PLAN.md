# Deep Learning-Driven API Attack Detection System (Business Demo Plan)

This document outlines a collaborative implementation plan for your 4-member capstone project team. Based on your feedback, this plan is heavily optimized for a **Business Leader Demo**. Business stakeholders want to see *visual impact* rather than raw code. 

To achieve this, we will build a "Victim" application (a vulnerable e-commerce site) and an "Attacker" simulation, alongside your AI security system.

## 1. The Demo Architecture (The "Showcase")

To wow business leaders, your presentation should follow this narrative:

1. **The Victim (Vulnerable E-commerce Site):** A simple storefront where users can log in, view products, and checkout. 
2. **The Attacker (Simulation Script):** A script running in the background generating three types of traffic:
   - *Normal:* Customers browsing.
   - *Known Attacks:* SQL Injections on the login page, Cross-Site Scripting (XSS) on product reviews.
   - *Anomalous:* Rapid credential stuffing (trying thousands of passwords).
3. **The Shield (Your AI Gateway):** Sits in front of the e-commerce site. It intercepts everything, analyzes it via ML, and blocks threats in real-time.
4. **The Command Center (Security Dashboard):** A sleek, dark-mode dashboard showing live traffic graphs (green vs. red), active threats, and "Explainable AI" insights (why a request was blocked).

## 2. Updated Role Division (4 Members)

We will distribute the new demo components among the team to maintain a balanced workload.

### Member 1: AI / Machine Learning Engineer
**Focus:** The Brains (Threat classification & Anomaly detection).
- **Tasks:**
  - Train a Deep Autoencoder (Anomaly Detection) and Hybrid CNN+BiLSTM (Threat Classification).
  - Use datasets that specifically contain e-commerce style attacks (SQLi, XSS, Path Traversal).
  - Serve the models via a fast inference API.

### Member 2: Gateway & Simulation Engineer
**Focus:** The Shield & The Attacker.
- **Tasks:**
  - Build the API Gateway to intercept traffic aimed at the e-commerce site.
  - Integrate Kafka to stream this traffic to the AI models.
  - **NEW:** Build the `attack_simulator.py` script that automatically fires normal, attack, and anomalous traffic at the gateway to run the live demo.

### Member 3: Backend & Integration Engineer
**Focus:** The Core Logic & The Victim Backend.
- **Tasks:**
  - Build the Risk Scoring Engine to evaluate ML predictions and enforce blocks via Redis.
  - **NEW:** Build the simple backend APIs for the Vulnerable E-commerce site (e.g., a dummy login endpoint, a fetch products endpoint).
  - Build the APIs that feed real-time metrics to the Security Dashboard.

### Member 4: Frontend Developer
**Focus:** The Visuals (Dashboard & Victim UI).
- **Tasks:**
  - Build the Security Dashboard (Next.js) with live charts and alert feeds.
  - **NEW:** Build a very simple, 2-page E-commerce UI (Storefront + Login page) so the audience has a visual context of what is being attacked.
  - Ensure the Dashboard has a premium, modern aesthetic (dark mode, glowing charts) to impress business leaders.

## 3. GitHub Collaborative Structure (Monorepo)

```text
capstone-api-security/
│
├── victim-ecommerce/       # (M3 & M4) Simple storefront UI & vulnerable backend APIs
│
├── attack-simulator/       # (M2) Python script to generate traffic for the demo
│
├── api-gateway/            # (M2) Intercepts traffic, checks Redis blocklist, sends to Kafka
│
├── ml-engine/              # (M1) AI Models, Feature Extraction, Inference API
│
├── security-backend/       # (M3) Risk Scorer, PostgreSQL DB, Dashboard API
│
├── security-dashboard/     # (M4) Next.js Command Center UI
│
├── shared/                 # Shared JSON schemas and types
│
└── docker-compose.yml      # Spins up everything for the local demo
```

## 4. Why this wins over Business Leaders

1. **Visual Storytelling:** Instead of showing terminal logs, you show a fake hacker trying to break into a store, and your dashboard lighting up in red to block them.
2. **Clear Value Proposition:** Business leaders understand "preventing e-commerce downtime and data breaches."
3. **Explainability (XAI):** By showing *why* the AI blocked a request (e.g., highlighting the exact SQL injection string in the dashboard), you build trust in the AI system.
