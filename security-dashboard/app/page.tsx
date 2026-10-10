'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KpiCards from '../components/KpiCards';
import LiveTrafficChart from '../components/LiveTrafficChart';
import ThreatRadar from '../components/ThreatRadar';
import VerdictFeed from '../components/VerdictFeed';
import VerdictDetailModal from '../components/VerdictDetailModal';
import AttackSimulatorPanel from '../components/AttackSimulatorPanel';
import BlocklistManager from '../components/BlocklistManager';
import TopologyMap from '../components/TopologyMap';

import {
  fetchBlocklist,
  fetchGatewayStats,
  fetchRecentVerdicts,
  EMPTY_STATS,
} from '../lib/api';
import { BlockedIPEntry, GatewayStats, RecentVerdict } from '../lib/types';
import { FEATURE_METADATA, highlightAttackPayload } from '../lib/xaiUtils';
import { ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [stats, setStats] = useState<GatewayStats>(EMPTY_STATS);
  const [verdicts, setVerdicts] = useState<RecentVerdict[]>([]);
  const [blockedIps, setBlockedIps] = useState<BlockedIPEntry[]>([]);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isBlocklistLive, setIsBlocklistLive] = useState<boolean>(false);
  const [selectedVerdict, setSelectedVerdict] = useState<RecentVerdict | null>(null);

  const [testUrl, setTestUrl] = useState('');
  const [testBody, setTestBody] = useState('');
  const [testResult, setTestResult] = useState<ReturnType<typeof highlightAttackPayload> | null>(null);

  const refreshTelemetry = useCallback(async () => {
    const statsRes = await fetchGatewayStats();
    const verdictsRes = await fetchRecentVerdicts();
    const blocklistRes = await fetchBlocklist();

    setStats(statsRes.data);
    setVerdicts(verdictsRes.data);
    setBlockedIps(blocklistRes.data);
    setIsLive(statsRes.isLive);
    setIsBlocklistLive(blocklistRes.isLive);
  }, []);

  useEffect(() => {
    refreshTelemetry();
    const interval = setInterval(refreshTelemetry, 3000);
    return () => clearInterval(interval);
  }, [refreshTelemetry]);

  const handleTestPayload = () => {
    setTestResult(highlightAttackPayload(`${testUrl}\n${testBody}`));
  };

  return (
    <div className="hub-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        blockedCount={blockedIps.length}
      />

      {/* Main Content Area */}
      <main className="hub-main">
        <Header
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onRefresh={refreshTelemetry}
          isLive={isLive}
        />

        {/* Dashboard overview */}
        {activeTab === 'dashboard' && (
          <>
            <KpiCards stats={stats} />
            <div className="dashboard-insights-grid">
              <LiveTrafficChart verdicts={verdicts} />
              <ThreatRadar verdicts={verdicts} />
            </div>
            <VerdictFeed
              verdicts={verdicts}
              onSelectVerdict={(v) => setSelectedVerdict(v)}
              searchFilter={searchQuery}
              isLive={isLive}
            />
          </>
        )}

        {/* 2. ATTACK STUDIO VIEW */}
        {activeTab === 'simulator' && <AttackSimulatorPanel />}

        {/* 3. LIVE STREAM VIEW */}
        {activeTab === 'verdicts' && (
          <VerdictFeed
            verdicts={verdicts}
            onSelectVerdict={(v) => setSelectedVerdict(v)}
            searchFilter={searchQuery}
            isLive={isLive}
          />
        )}

        {/* 4. EXPLAINABLE AI VIEW */}
        {activeTab === 'xai' && (
          <div className="white-card">
            <div className="card-header-row">
              <div>
                <h3 className="card-title">Explainable AI features</h3>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Model feature reference and payload pattern preview
                </span>
              </div>
            </div>

            {/* Sandbox */}
            <div
              style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-lg)',
                background: '#f8fafc',
                border: '1px solid var(--border-light)',
                marginBottom: '1.5rem',
              }}
            >
              <h4 style={{ fontSize: '0.92rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Local payload pattern preview
              </h4>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Checks the endpoint and body for known attack-pattern strings. This is a client-side preview, not model inference.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Target Endpoint
                  </label>
                  <input
                    type="text"
                    value={testUrl}
                    placeholder="/api/endpoint"
                    onChange={(e) => setTestUrl(e.target.value)}
                    className="hub-search-input font-mono"
                    style={{ width: '100%', paddingLeft: '1rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Payload Body
                  </label>
                  <input
                    type="text"
                    value={testBody}
                    placeholder="Enter a request body to inspect"
                    onChange={(e) => setTestBody(e.target.value)}
                    className="hub-search-input font-mono"
                    style={{ width: '100%', paddingLeft: '1rem' }}
                  />
                </div>
              </div>

              <button className="hub-btn-primary" onClick={handleTestPayload}>
                <span>Check for known patterns</span>
                <ArrowRight size={14} />
              </button>

              {testResult && (
                <div
                  style={{
                    marginTop: '1.25rem',
                    padding: '1rem',
                    background: '#ffffff',
                    border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <strong style={{ fontSize: '0.85rem' }}>
                    {testResult.hasSuspiciousTokens
                      ? 'Known pattern strings found'
                      : 'No known pattern strings found'}
                  </strong>
                  {testResult.tokens.length > 0 && (
                    <ul className="pattern-token-list">
                      {testResult.tokens.map((token) => <li key={token}>{token}</li>)}
                    </ul>
                  )}
                </div>
              )}
            </div>

            {/* 18 Features Table */}
            <h4 style={{ fontSize: '0.92rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              18-Dimensional Feature Vector Taxonomy
            </h4>
            <div style={{ overflowX: 'auto' }}>
              <table className="hub-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Identifier</th>
                    <th>Description</th>
                    <th>Clean Baseline</th>
                    <th>Unit</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(FEATURE_METADATA).map(([k, m], i) => (
                    <tr key={k}>
                      <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                      <td className="font-mono" style={{ color: '#0284c7', fontWeight: 600 }}>{k}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{m.description}</td>
                      <td className="font-mono" style={{ color: '#16a34a' }}>{m.normalBaseline}</td>
                      <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{m.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 5. REDIS BLOCKLIST VIEW */}
        {activeTab === 'blocklist' && (
          <BlocklistManager
            blockedIps={blockedIps}
            onRefreshList={refreshTelemetry}
            isLive={isBlocklistLive}
          />
        )}

        {/* 6. SYSTEM TOPOLOGY VIEW */}
        {activeTab === 'topology' && <TopologyMap />}

      </main>

      {/* Forensic Dossier Modal */}
      <VerdictDetailModal
        verdict={selectedVerdict}
        onClose={() => setSelectedVerdict(null)}
        onBlockIpSuccess={() => refreshTelemetry()}
      />
    </div>
  );
}
