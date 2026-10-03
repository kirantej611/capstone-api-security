'use client';

import React from 'react';
import { RecentVerdict } from '../lib/types';

interface RecentMessagesCardProps {
  verdicts: RecentVerdict[];
  onSelectVerdict?: (v: RecentVerdict) => void;
  onViewAll?: () => void;
}

export default function RecentMessagesCard({
  verdicts,
  onSelectVerdict,
  onViewAll,
}: RecentMessagesCardProps) {
  const topBlocked = verdicts.filter((v) => v.action === 'BLOCK').slice(0, 3);

  const fallbackItems = [
    {
      name: 'Dr. Lila Ramirez',
      ip: '198.51.100.42',
      threat: 'SQL Injection',
      time: '9:00 AM',
      color: '#f43f5e',
    },
    {
      name: 'Markus Chen',
      ip: '203.0.113.88',
      threat: 'Stored XSS',
      time: '8:45 AM',
      color: '#8b5cf6',
    },
    {
      name: 'Elena Rostova',
      ip: '185.220.101.5',
      threat: 'Path Traversal',
      time: '8:12 AM',
      color: '#0284c7',
    },
  ];

  return (
    <div className="white-card">
      <div className="card-header-row">
        <h3 className="card-title">Messages</h3>
        <button
          onClick={onViewAll}
          style={{
            background: 'transparent',
            border: 'none',
            fontSize: '0.74rem',
            color: 'var(--text-muted)',
            cursor: 'pointer',
          }}
        >
          View All
        </button>
      </div>

      <div className="messages-list">
        {fallbackItems.map((item, idx) => (
          <div
            key={idx}
            className="message-item"
            style={{ cursor: 'pointer' }}
            onClick={() => {
              if (topBlocked[idx] && onSelectVerdict) {
                onSelectVerdict(topBlocked[idx]);
              }
            }}
          >
            <div className="message-user-wrap">
              <div
                className="message-avatar"
                style={{
                  background: item.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: '0.72rem',
                }}
              >
                {item.name.charAt(0)}
              </div>

              <div>
                <div className="message-name">{item.name}</div>
                <div className="message-meta font-mono">
                  {item.threat} • {item.ip}
                </div>
              </div>
            </div>

            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {item.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
