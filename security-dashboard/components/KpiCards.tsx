'use client';

import React from 'react';
import { Activity, Ban, CheckCircle2, Clock3, Shield, Gauge } from 'lucide-react';
import { GatewayStats } from '../lib/types';

interface KpiCardsProps {
  stats: GatewayStats;
}

export default function KpiCards({ stats }: KpiCardsProps) {
  const cards = [
    {
      id: 'total-requests',
      icon: Activity,
      value: stats.total_requests.toLocaleString(),
      label: 'Total requests',
    },
    {
      id: 'blocked-requests',
      icon: Ban,
      value: stats.blocked_requests.toLocaleString(),
      label: 'Blocked requests',
    },
    {
      id: 'allowed-requests',
      icon: CheckCircle2,
      value: stats.allowed_requests.toLocaleString(),
      label: 'Allowed requests',
    },
    {
      id: 'inference-latency',
      icon: Clock3,
      value: `${stats.avg_ml_latency_ms.toFixed(1)} ms`,
      label: 'Average ML latency',
    },
    {
      id: 'active-blocklist',
      icon: Shield,
      value: stats.active_blocked_ips.toLocaleString(),
      label: 'Active blocked IPs',
    },
    {
      id: 'request-rate',
      icon: Gauge,
      value: `${stats.requests_per_second.toFixed(1)} / sec`,
      label: 'Current request rate',
    },
  ];

  return (
    <div className="pastel-cards-grid">
      {cards.map(({ id, icon: Icon, value, label }) => (
        <div key={id} className="pastel-card">
          <div className="pastel-card-top">
            <Icon size={18} aria-hidden="true" />
          </div>
          <div>
            <div className="pastel-card-number">{value}</div>
            <div className="pastel-card-label">{label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
