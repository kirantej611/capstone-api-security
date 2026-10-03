'use client';

import React from 'react';
import {
  ShieldCheck,
  ShieldBan,
  Timer,
  Server,
  Zap,
  Cpu,
  TrendingUp,
} from 'lucide-react';
import { GatewayStats } from '../lib/types';

interface KpiCardsProps {
  stats: GatewayStats;
}

export default function KpiCards({ stats }: KpiCardsProps) {
  const blockRate = stats.total_requests > 0
    ? ((stats.blocked_requests / stats.total_requests) * 100).toFixed(1)
    : '0.0';

  const cards = [
    {
      id: 'total',
      title: 'Total Traffic Intercepted',
      value: stats.total_requests.toLocaleString(),
      unit: 'reqs',
      subtitle: `${stats.requests_per_second.toFixed(1)} req/s current throughput`,
      icon: ShieldCheck,
      glow: 'rgba(59, 130, 246, 0.25)',
      color: '#3b82f6',
    },
    {
      id: 'blocked',
      title: 'Threats Neutralized',
      value: stats.blocked_requests.toLocaleString(),
      unit: `(${blockRate}%)`,
      subtitle: `${stats.rate_limited_requests} rate-limited • ${stats.flagged_requests} flagged`,
      icon: ShieldBan,
      glow: 'rgba(239, 68, 68, 0.3)',
      color: '#ef4444',
    },
    {
      id: 'latency',
      title: 'Neural Inference Latency',
      value: stats.avg_ml_latency_ms.toFixed(2),
      unit: 'ms',
      subtitle: 'CNN+BiLSTM + Deep Autoencoder',
      icon: Timer,
      glow: 'rgba(16, 185, 129, 0.25)',
      color: '#10b981',
    },
    {
      id: 'blocklist',
      title: 'Active Redis Blocklist',
      value: stats.active_blocked_ips.toString(),
      unit: 'IPs',
      subtitle: 'Sliding 3600s TTL per violation',
      icon: Server,
      glow: 'rgba(245, 158, 11, 0.25)',
      color: '#f59e0b',
    },
    {
      id: 'rps',
      title: 'Traffic Velocity (RPS)',
      value: stats.requests_per_second.toFixed(1),
      unit: 'req/s',
      subtitle: 'Sliding 60s measurement window',
      icon: Zap,
      glow: 'rgba(6, 182, 212, 0.25)',
      color: '#06b6d4',
    },
    {
      id: 'anomaly',
      title: 'Model Anomaly Baseline',
      value: '0.041',
      unit: '/ 0.280',
      subtitle: 'Threshold: 0.280 reconstruction err',
      icon: Cpu,
      glow: 'rgba(139, 92, 246, 0.25)',
      color: '#8b5cf6',
    },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.id}
            className="glass-panel kpi-card"
            style={{ ['--kpi-glow' as any]: c.glow }}
          >
            <div className="kpi-top">
              <span className="kpi-title">{c.title}</span>
              <div
                className="kpi-icon-wrap"
                style={{ color: c.color, background: `${c.color}15` }}
              >
                <Icon size={16} />
              </div>
            </div>

            <div className="kpi-value-row">
              <span className="kpi-value">{c.value}</span>
              <span className="kpi-unit font-mono">{c.unit}</span>
            </div>

            <div className="kpi-footer font-mono">
              <TrendingUp size={12} color="var(--text-dim)" />
              <span>{c.subtitle}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
