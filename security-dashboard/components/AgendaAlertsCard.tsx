'use client';

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface AgendaAlertsCardProps {
  onSelectAlert?: (title: string) => void;
}

export default function AgendaAlertsCard({ onSelectAlert }: AgendaAlertsCardProps) {
  const alerts = [
    {
      id: '1',
      time: '08:00 am',
      colorClass: 'lavender',
      tag: 'Critical Severity • Port 8080',
      title: 'SQL Injection on /api/login',
    },
    {
      id: '2',
      time: '10:00 am',
      colorClass: 'yellow',
      tag: 'High Risk • XSS Vector Dropped',
      title: 'Stored XSS on /api/reviews',
    },
    {
      id: '3',
      time: '10:30 am',
      colorClass: 'cyan',
      tag: 'Reconstruction Error 0.94 > 0.28',
      title: 'Path Traversal /etc/shadow Blocked',
    },
  ];

  return (
    <div className="white-card">
      <div className="card-header-row">
        <h3 className="card-title">Agenda</h3>
        <button className="card-dots-btn">•••</button>
      </div>

      <div className="agenda-list">
        {alerts.map((item) => (
          <div
            key={item.id}
            className={`agenda-item ${item.colorClass}`}
            onClick={() => onSelectAlert && onSelectAlert(item.title)}
            style={{ cursor: 'pointer' }}
          >
            <div className="agenda-time-pill">{item.time}</div>

            <div className="agenda-content">
              <span className="agenda-tag">{item.tag}</span>
              <div className="agenda-title">{item.title}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
