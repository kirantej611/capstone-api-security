# Security Dashboard — Neural Command Center (Member 4)

The executive command center and real-time visualization layer of the **Deep Learning-Driven API Attack Detection System**. Designed specifically for **Business Leader Demos** to deliver visual impact, Explainable AI (XAI) confidence, and A/B defense proof.

---

## Key Capabilities

1. **Executive KPI Strip**: Real-time traffic volume, threats blocked, block rate %, neural inference latency (CNN+BiLSTM + Autoencoder rolling avg ~3.6ms), active Redis blocklist count, and velocity (RPS).
2. **Real-time Dual-Line SVG Traffic Chart**: Interactive timeline comparing legitimate customer traffic against blocked attacks with latency jitter and hover tooltip forensics.
3. **Multi-Class Threat Radar**: Visual distribution breakdown across SQL Injection (CWE-89), Cross-Site Scripting (CWE-79), Path Traversal (CWE-22), OS Command Injection (CWE-78), and Credential Stuffing (CWE-307).
4. **Live Threat Interception Feed**: Real-time tabular stream of intercepted HTTP requests with filtering (All, Blocked, Allowed, Rate-Limited), search by IP/URL, and row click inspection.
5. **Explainable AI (XAI) Forensic Dossier**:
   - Deep Autoencoder reconstruction error gauge vs threshold (0.280 baseline).
   - Hybrid CNN+BiLSTM multi-class probability breakdown with percentage bars.
   - Top contributing feature delta bars out of 18 extracted dimensions (e.g. `num_sql_keywords`, `payload_entropy`).
   - Raw HTTP payload body with inline highlighted exploit substrings.
6. **Attack Simulation Studio (Business Demo Suite)**:
   - 6 pre-configured attack scenarios.
   - **A/B Protection Switch**: Fire attacks *With AI Shield Gateway (:8080)* vs *Direct to Vulnerable Victim (:8081)*.
   - 30-Second Automated Executive Demo Narrative button.
7. **Redis Perimeter Blocklist Manager**: Real-time table of banned IPs with sliding 3600s TTL countdowns, manual ban inputs, and one-click unban.
8. **Victim E-Commerce Storefront (2-Page Visual Showcase)**:
   - Storefront catalog with products, category filters, search bar, shopping cart, and review submission.
   - Authentication / Login page with one-click legitimate user vs SQLi bypass pre-fills.
   - Protection Mode switcher showing instant 403 Forbidden protection vs database breach.
9. **System Topology**: Interactive microservice dataflow diagram detailing Member 1, Member 2, Member 3, and Member 4 subsystems.
10. **Resilient Dual-Mode Engine**: Automatically connects to live Gateway (`:8080`) when running, and gracefully transitions to the interactive high-fidelity demo engine when offline.

---

## Tech Stack

- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Curated Dark Cyber Design System (Obsidian/Slate palette, Glassmorphism, Monospace Data Fonts, Responsive SVG Data Visualizations)
- **Icons**: Lucide React
- **Integration**: REST APIs to API Gateway (`:8080`) & Victim Backend (`:8081`)

---

## Getting Started

### 1. Prerequisites
- Node.js 18+ (tested on Node v20 LTS)
- npm 9+

### 2. Installation
```bash
cd security-dashboard
npm install
```

### 3. Running Locally
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Production Build
```bash
npm run build
npm start
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_GATEWAY_URL` | `http://localhost:8080` | URL of Member 2's API Gateway Shield |
| `NEXT_PUBLIC_VICTIM_URL` | `http://localhost:8081` | URL of Member 3's Victim E-Commerce Backend |
