# Deep Learning-Driven API Attack Detection System

This repository contains the source code for the capstone project: **Deep Learning-Driven API Attack Detection, Prevention and Adaptive Security System for Cloud-Native Microservices**.

## Team Members
* Kirantej T R (1BM23IS124)
* Kishan M Dev (1BM23IS126)
* Koushik B Hegde (1BM23IS129)
* Nikhil Amruth B (1BM24IS413)

## Repository Structure

This is a monorepo containing multiple microservices:

* `api-gateway/`: Intercepts traffic and publishes to Kafka.
* `attack-simulator/`: Python script to generate normal/malicious traffic for demos.
* `ml-engine/`: Deep learning models (CNN, BiLSTM, Autoencoder) for anomaly detection.
* `security-backend/`: Risk scoring, database management, and API for the dashboard.
* `security-dashboard/`: Next.js frontend for real-time monitoring and XAI.
* `victim-ecommerce/`: A vulnerable e-commerce application to serve as a demo target.
* `shared/`: Shared JSON schemas, proto files, and common utilities.

## Prerequisites
* Docker & Docker Compose
* Node.js (for frontend)
* Python 3.11+ (for backend and ML)

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/kirantej611/capstone-api-security.git
   cd capstone-api-security
   ```

2. Start the local infrastructure (Kafka, Redis, Postgres):
   ```bash
   docker-compose up -d
   ```
