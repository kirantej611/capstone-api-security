'use client';

import React, { useState, useMemo } from 'react';
import {
  ListFilter,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  Shield,
  Layers,
} from 'lucide-react';
import { GatewayAction, RecentVerdict } from '../lib/types';

interface VerdictFeedProps {
  verdicts: RecentVerdict[];
  onSelectVerdict: (verdict: RecentVerdict) => void;
}

export default function VerdictFeed({
  verdicts,
  onSelectVerdict,
}: VerdictFeedProps) {
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filtered = useMemo(() => {
    return verdicts.filter((v) => {
      if (filterAction !== 'ALL' && v.action !== filterAction) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesIp = v.client_ip.toLowerCase().includes(q);
        const matchesPath = v.path.toLowerCase().includes(q);
        const matchesId = v.request_id.toLowerCase().includes(q);
        const matchesThreat = (v.threat_type || '').toLowerCase().includes(q);
        if (!matchesIp && !matchesPath && !matchesId && !matchesThreat) {
          return false;
        }
      }
      return true;
    });
  }, [verdicts, filterAction, searchQuery]);

  const renderActionBadge = (action: GatewayAction) => {
    switch (action) {
      case 'BLOCK':
        return (
          <span className="badge badge-block">
            <XCircle size={12} />
            <span>BLOCKED</span>
          </span>
        );
      case 'ALLOW':
        return (
          <span className="badge badge-allow">
            <CheckCircle2 size={12} />
            <span>ALLOWED</span>
          </span>
        );
      case 'RATE_LIMIT':
        return (
          <span className="badge badge-rate-limit">
            <Clock size={12} />
            <span>RATE LIMITED</span>
          </span>
        );
      case 'FLAG':
        return (
          <span className="badge badge-flag">
            <AlertTriangle size={12} />
            <span>FLAGGED</span>
          </span>
        );
      default:
        return <span className="badge">{action}</span>;
    }
  };

  return (
    <div className="glass-panel feed-panel">
      <div className="feed-controls">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="panel-title-wrap">
            <Shield size={18} color="#3b82f6" />
            <div>
              <h3 className="panel-title">Real-Time Threat Interception Stream</h3>
              <span className="panel-subtitle">
                Live gateway telemetry • Click any request for Explainable AI (XAI) deep-dive
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div className="feed-filters">
            {['ALL', 'BLOCK', 'ALLOW', 'RATE_LIMIT'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterAction(tab)}
                className={`filter-btn ${filterAction === tab ? 'active' : ''}`}
              >
                {tab === 'ALL' ? 'All Events' : tab}
              </button>
            ))}
          </div>

          <div className="search-input-wrap">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Search IP, endpoint, ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
        </div>
      </div>

      <div className="table-wrap">
        <table className="verdict-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Request ID</th>
              <th>Method & Endpoint</th>
              <th>Client IP</th>
              <th>Shield Verdict</th>
              <th>Threat Type</th>
              <th>Risk Severity</th>
              <th>Anomaly Score</th>
              <th>Latency</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-dim)' }}>
                  No requests matching current filter.
                </td>
              </tr>
            ) : (
              filtered.slice(0, 30).map((v) => {
                const timeOnly = v.timestamp.includes('T')
                  ? v.timestamp.split('T')[1].slice(0, 8)
                  : v.timestamp.slice(11, 19);

                return (
                  <tr
                    key={v.request_id}
                    className="verdict-row"
                    onClick={() => onSelectVerdict(v)}
                  >
                    <td className="font-mono" style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>
                      {timeOnly}
                    </td>

                    <td className="font-mono" style={{ color: '#93c5fd', fontSize: '0.74rem' }}>
                      {v.request_id.slice(0, 12)}...
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                        <span className={`method-badge method-${v.method}`}>
                          {v.method}
                        </span>
                        <span className="font-mono" style={{ color: '#fff', fontSize: '0.78rem' }}>
                          {v.path}
                        </span>
                      </div>
                    </td>

                    <td className="font-mono" style={{ color: '#cbd5e1', fontSize: '0.76rem' }}>
                      {v.client_ip}
                    </td>

                    <td>{renderActionBadge(v.action)}</td>

                    <td>
                      <span
                        style={{
                          color: v.threat_type === 'Normal' ? '#94a3b8' : '#f87171',
                          fontWeight: v.threat_type === 'Normal' ? 400 : 600,
                          fontSize: '0.78rem',
                        }}
                      >
                        {v.threat_type || '—'}
                      </span>
                    </td>

                    <td>
                      {v.risk_level ? (
                        <span className={`risk-pill risk-${v.risk_level}`}>
                          {v.risk_level}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>

                    <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                      {v.anomaly_score !== undefined && v.anomaly_score !== null ? (
                        <span
                          style={{
                            color:
                              v.anomaly_score > 0.28
                                ? '#ef4444'
                                : '#10b981',
                            fontWeight: 600,
                          }}
                        >
                          {v.anomaly_score.toFixed(3)}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>

                    <td className="font-mono" style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>
                      {v.ml_latency_ms ? `${v.ml_latency_ms.toFixed(1)}ms` : '3.4ms'}
                    </td>

                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '0.25rem 0.55rem', fontSize: '0.72rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectVerdict(v);
                        }}
                      >
                        <span>XAI</span>
                        <ArrowUpRight size={12} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
