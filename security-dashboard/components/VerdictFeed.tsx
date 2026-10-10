'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  Shield,
} from 'lucide-react';
import { GatewayAction, RecentVerdict } from '../lib/types';
import { formatIstTime } from '../lib/formatters';

interface VerdictFeedProps {
  verdicts: RecentVerdict[];
  onSelectVerdict: (verdict: RecentVerdict) => void;
  isLive: boolean;
}

export default function VerdictFeed({
  verdicts,
  onSelectVerdict,
  isLive,
}: VerdictFeedProps) {
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [internalQuery, setInternalQuery] = useState<string>('');

  const filtered = useMemo(() => {
    return verdicts.filter((v) => {
      if (filterAction !== 'ALL' && v.action !== filterAction) {
        return false;
      }
      if (internalQuery.trim()) {
        const q = internalQuery.trim().toLowerCase();
        const matchesIp = v.client_ip.toLowerCase().includes(q);
        const matchesPath = v.path.toLowerCase().includes(q);
        const matchesId = v.request_id.toLowerCase().includes(q);
        const matchesMethod = v.method.toLowerCase().includes(q);
        const matchesThreat = (v.threat_type || '').toLowerCase().includes(q);
        if (!matchesIp && !matchesPath && !matchesId && !matchesMethod && !matchesThreat) {
          return false;
        }
      }
      return true;
    });
  }, [verdicts, filterAction, internalQuery]);

  const renderBadge = (action: GatewayAction) => {
    switch (action) {
      case 'BLOCK':
        return <span className="hub-badge hub-badge-block">BLOCKED</span>;
      case 'ALLOW':
        return <span className="hub-badge hub-badge-allow">ALLOWED</span>;
      case 'RATE_LIMIT':
        return <span className="hub-badge hub-badge-rate">RATE LIMIT</span>;
      case 'FLAG':
        return <span className="hub-badge hub-badge-rate">FLAGGED</span>;
      default:
        return <span className="hub-badge">{action}</span>;
    }
  };

  return (
    <div className="white-card" style={{ marginTop: '1.5rem' }}>
      <div className="card-header-row" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 className="card-title">Real-Time Threat Interception Stream</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            {isLive
              ? 'Gateway verdicts • Select a row to inspect the available request and model details.'
              : 'Gateway offline • Only locally simulated requests appear here; no sample telemetry is loaded.'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label className="hub-search-box verdict-search-box">
            <Search size={16} className="hub-search-icon" />
            <input
              type="search"
              placeholder="Search requests, IPs, or paths..."
              value={internalQuery}
              onChange={(event) => setInternalQuery(event.target.value)}
              className="hub-search-input"
              aria-label="Search verdicts by request ID, method, IP, path, or threat"
            />
          </label>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {['ALL', 'BLOCK', 'ALLOW', 'RATE_LIMIT', 'FLAG'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterAction(tab)}
                className="select-pill"
                style={{
                  background: filterAction === tab ? 'var(--accent-cyan-light)' : '#f8fafc',
                  color: filterAction === tab ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  fontWeight: filterAction === tab ? 600 : 400,
                  borderColor: filterAction === tab ? '#bae6fd' : 'var(--border-light)',
                }}
              >
                {tab === 'ALL'
                  ? 'All'
                  : tab === 'BLOCK'
                    ? 'Blocked'
                    : tab === 'ALLOW'
                      ? 'Allowed'
                      : tab === 'RATE_LIMIT'
                        ? 'Rate limited'
                        : 'Flagged'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="hub-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Request ID</th>
              <th>Method & Endpoint</th>
              <th>Client IP</th>
              <th>Verdict</th>
              <th>Threat Type</th>
              <th>Anomaly Score</th>
              <th>Latency</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 15).map((v) => {
              return (
                <tr
                  key={v.request_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSelectVerdict(v)}
                >
                  <td className="font-mono" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {formatIstTime(v.timestamp)}
                  </td>

                  <td className="font-mono" style={{ color: '#0284c7', fontSize: '0.75rem' }}>
                    {v.request_id.slice(0, 12)}...
                  </td>

                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '2px 5px',
                          borderRadius: '4px',
                          background: v.method === 'POST' ? '#dcfce7' : '#e0f2fe',
                          color: v.method === 'POST' ? '#16a34a' : '#0284c7',
                        }}
                      >
                        {v.method}
                      </span>
                      <span className="font-mono" style={{ fontSize: '0.78rem' }}>{v.path}</span>
                    </div>
                  </td>

                  <td className="font-mono" style={{ fontSize: '0.76rem', color: '#475569' }}>
                    {v.client_ip}
                  </td>

                  <td>{renderBadge(v.action)}</td>

                  <td>
                    <span
                      style={{
                        color: v.threat_type === 'Normal' ? '#64748b' : '#ef4444',
                        fontWeight: v.threat_type === 'Normal' ? 400 : 600,
                        fontSize: '0.78rem',
                      }}
                    >
                      {v.threat_type || '—'}
                    </span>
                  </td>

                  <td className="font-mono" style={{ fontSize: '0.76rem' }}>
                    <span
                      style={{
                        color: v.anomaly_score == null
                          ? 'var(--text-muted)'
                          : v.action === 'BLOCK'
                          ? '#ef4444'
                          : '#16a34a',
                        fontWeight: 600,
                      }}
                    >
                      {v.anomaly_score == null ? '—' : v.anomaly_score.toFixed(3)}
                    </span>
                  </td>

                  <td className="font-mono" style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    {v.ml_latency_ms == null ? '—' : `${v.ml_latency_ms.toFixed(1)}ms`}
                  </td>

                  <td>
                    <button
                      className="hub-btn-secondary"
                      style={{ padding: '0.25rem 0.65rem', fontSize: '0.72rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectVerdict(v);
                      }}
                    >
                      <span>Inspect</span>
                      <ArrowUpRight size={12} />
                    </button>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="dashboard-empty-state">
                  No requests match the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
