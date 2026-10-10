'use client';

import React from 'react';
import { Target, Database, FileCode, FolderGit2, Terminal, Users } from 'lucide-react';
import { RecentVerdict } from '../lib/types';

interface ThreatRadarProps {
  verdicts: RecentVerdict[];
}

export default function ThreatRadar({ verdicts }: ThreatRadarProps) {
  const threatStats = verdicts.reduce<Record<string, number>>((acc, verdict) => {
    if (verdict.threat_type && verdict.threat_type !== 'Normal') {
      acc[verdict.threat_type] = (acc[verdict.threat_type] || 0) + 1;
    }
    return acc;
  }, {});

  const totalThreats = Object.values(threatStats).reduce((a, b) => a + b, 0);

  const threatMetadata: Record<string, { label: string; color: string; icon: typeof Database; cwe?: string }> = {
    SQLi: { label: 'SQL Injection', color: '#ef4444', icon: Database, cwe: 'CWE-89' },
    XSS: { label: 'Cross-Site Scripting', color: '#f59e0b', icon: FileCode, cwe: 'CWE-79' },
    'Path Traversal': { label: 'Directory Traversal', color: '#8b5cf6', icon: FolderGit2, cwe: 'CWE-22' },
    'Command Injection': { label: 'OS Command Injection', color: '#ec4899', icon: Terminal, cwe: 'CWE-78' },
    'Credential Stuffing': { label: 'Credential Stuffing', color: '#06b6d4', icon: Users, cwe: 'CWE-307' },
    'BOLA / Broken Object Auth': {
      label: 'Broken Object Level Authorization',
      color: '#14b8a6',
      icon: Target,
    },
  };
  const threatConfig = Object.entries(threatStats)
    .map(([type, count]) => ({
      type,
      count,
      ...(threatMetadata[type] || { label: type, color: '#64748b', icon: Target }),
    }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="white-card">
      <div className="card-header-row">
        <div className="panel-title-wrap">
          <Target size={18} color="#ef4444" />
          <div>
            <h3 className="card-title">Threat types</h3>
            <span className="dashboard-subtitle">From the currently available verdicts</span>
          </div>
        </div>
        <span
          className="hub-badge hub-badge-block"
        >
          {totalThreats} {totalThreats === 1 ? 'threat' : 'threats'}
        </span>
      </div>

      {totalThreats > 0 && (
        <div
          style={{
            width: '100%',
            height: '10px',
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '999px',
            display: 'flex',
            overflow: 'hidden',
            margin: '0.75rem 0',
          }}
          aria-label="Threat type distribution"
        >
          {threatConfig.map((item) => {
            const pct = (item.count / totalThreats) * 100;
            return (
              <div
                key={item.type}
                title={`${item.label}: ${item.count} (${pct.toFixed(1)}%)`}
                style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: item.color,
                  transition: 'width 0.5s ease',
                }}
              />
            );
          })}
        </div>
      )}

      {totalThreats === 0 ? (
        <p className="dashboard-empty-state">No threat events in the available telemetry.</p>
      ) : (
      <div className="threat-list">
        {threatConfig.map((item) => {
          const Icon = item.icon;
          const pct = ((item.count / totalThreats) * 100).toFixed(1);

          return (
            <div key={item.type} className="threat-row">
              <div className="threat-label">
                <span
                  style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '6px',
                    background: `${item.color}20`,
                    color: item.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Icon size={14} />
                </span>
                <div>
                  <div style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>
                    {item.label}
                  </div>
                  {item.cwe && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', fontFamily: 'var(--font-mono)' }}>
                      {item.cwe}
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {pct}%
                </span>
                <span
                  className="threat-count-pill"
                  style={{ color: item.color, border: `1px solid ${item.color}40` }}
                >
                  {item.count}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      )}
    </div>
  );
}
