# Security Dashboard

The frontend dashboard for the **Deep Learning-Driven API Attack Detection System**. Operational metrics, verdicts, threat summaries, and blocklist entries are read from the configured API gateway.

---

## Key Capabilities

1. **Telemetry overview**: Request totals, allowed and blocked requests, ML latency, active blocked IPs, and request rate from gateway statistics.
2. **Recent request activity**: Allowed, blocked, and other verdicts bucketed from the available verdict timestamps; no generated chart data.
3. **Threat type summary**: Counts and percentages derived from the currently available gateway verdicts.
4. **Verdict feed**: Search and filter by action, inspect individual requests, and open the XAI forensic details.
5. **Explainable AI reference**: Feature metadata and a client-side pattern preview, clearly separated from actual model inference.
6. **Attack simulation studio**: Preconfigured scenarios can be sent through the shield or directly to the victim backend. When those services are unavailable, its documented local demo fallback may return simulated results.
7. **IP blocklist manager**: Add and remove entries. Only fields returned by the gateway are shown; unavailable TTL, severity, and timestamps are not fabricated.
8. **Victim storefront and system topology**: Separate dashboard views for the demo application and service map.

When gateway telemetry is unavailable, dashboard metrics and lists start empty and the connection status is shown. The dashboard does not substitute seeded traffic or sample metrics for live data.

---

## Tech Stack

- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Responsive light dashboard theme with SVG data visualizations
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
