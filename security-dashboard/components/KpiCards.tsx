'use client';

import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { GatewayStats } from '../lib/types';

interface KpiCardsProps {
  stats: GatewayStats;
}

export default function KpiCards({ stats }: KpiCardsProps) {
  const cards = [
    {
      id: 'students',
      colorClass: 'purple',
      badge: '↑ 15%',
      badgeType: 'positive',
      value: stats.total_requests.toLocaleString(),
      label: 'Total Traffic (Requests)',
    },
    {
      id: 'teachers',
      colorClass: 'yellow',
      badge: '↓ 3%',
      badgeType: 'warning',
      value: stats.blocked_requests.toLocaleString(),
      label: 'Blocked Threat Vectors',
    },
    {
      id: 'staffs',
      colorClass: 'blue',
      badge: '↓ 3%',
      badgeType: 'neutral',
      value: `${stats.avg_ml_latency_ms.toFixed(1)}ms`,
      label: 'ML Inference Latency',
    },
    {
      id: 'awards',
      colorClass: 'orange',
      badge: '↑ 5%',
      badgeType: 'positive',
      value: stats.active_blocked_ips.toString(),
      label: 'Active Redis Blocklist',
    },
  ];

  return (
    <div className="pastel-cards-grid">
      {cards.map((c) => (
        <div key={c.id} className={`pastel-card ${c.colorClass}`}>
          <div className="pastel-card-top">
            <span className={`pastel-badge ${c.badgeType}`}>
              {c.badge}
            </span>
            <button className="card-dots-btn">•••</button>
          </div>

          <div>
            <div className="pastel-card-number">{c.value}</div>
            <div className="pastel-card-label">{c.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
