'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KpiCards from '../components/KpiCards';
import DonutChartCard from '../components/DonutChartCard';
import AttendanceChartCard from '../components/AttendanceChartCard';
import CalendarStrip from '../components/CalendarStrip';
import AgendaAlertsCard from '../components/AgendaAlertsCard';
import RecentMessagesCard from '../components/RecentMessagesCard';
import VerdictFeed from '../components/VerdictFeed';
import VerdictDetailModal from '../components/VerdictDetailModal';
import AttackSimulatorPanel from '../components/AttackSimulatorPanel';
import BlocklistManager from '../components/BlocklistManager';
import StorefrontPreview from '../components/StorefrontPreview';
import TopologyMap from '../components/TopologyMap';

import {
  fetchBlocklist,
  fetchGatewayStats,
  fetchRecentVerdicts,
  localStore,
} from '../lib/api';
import { BlockedIPEntry, GatewayStats, RecentVerdict } from '../lib/types';
import { INITIAL_STATS, INITIAL_VERDICTS, INITIAL_BLOCKED_IPS } from '../lib/mockData';
import { FEATURE_METADATA } from '../lib/xaiUtils';
import { Cpu, ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [stats, setStats] = useState<GatewayStats>(INITIAL_STATS);
  const [verdicts, setVerdicts] = useState<RecentVerdict[]>(INITIAL_VERDICTS);
  const [blockedIps, setBlockedIps] = useState<BlockedIPEntry[]>(INITIAL_BLOCKED_IPS);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(true);
  const [selectedVerdict, setSelectedVerdict] = useState<RecentVerdict | null>(null);

  // XAI Sandbox state
  const [testUrl, setTestUrl] = useState('/api/login');
  const [testBody, setTestBody] = useState('{"username": "admin\' OR \'1\'=\'1\' --", "password": "123"}');
  const [testResult, setTestResult] = useState<any>(null);

  const refreshTelemetry = useCallback(async () => {
    const statsRes = await fetchGatewayStats();
    const verdictsRes = await fetchRecentVerdicts();
    const blocklistRes = await fetchBlocklist();

    setStats(statsRes.data);
    setVerdicts(verdictsRes.data);
    setBlockedIps(blocklistRes.data);
    setIsLive(statsRes.isLive);
  }, []);

  useEffect(() => {
    refreshTelemetry();
    const interval = setInterval(refreshTelemetry, 3000);
    return () => clearInterval(interval);
  }, [refreshTelemetry]);

  // Periodic streaming events
  useEffect(() => {
    if (!isStreaming) return;

    const streamInterval = setInterval(() => {
      const isAttack = Math.random() > 0.75;
      const attackTypes: ('SQLi' | 'XSS' | 'Path Traversal' | 'Command Injection')[] = [
        'SQLi',
        'XSS',
        'Path Traversal',
        'Command Injection',
      ];
      const randomThreat = attackTypes[Math.floor(Math.random() * attackTypes.length)];

      const endpoints = [
        '/api/products',
        '/api/products/4',
        '/api/search?q=wireless+mouse',
        '/api/cart',
        '/api/products/2/reviews',
      ];
      const chosenEndpoint = isAttack
        ? randomThreat === 'SQLi'
          ? '/api/login'
          : randomThreat === 'XSS'
          ? '/api/products/1/reviews'
          : randomThreat === 'Path Traversal'
          ? '/api/download?file=../../../../etc/passwd'
          : '/api/ping'
        : endpoints[Math.floor(Math.random() * endpoints.length)];

      const newVerdict: RecentVerdict = {
        request_id: `req_${Math.random().toString(36).substring(2, 11)}`,
        timestamp: new Date().toISOString(),
        client_ip: isAttack
          ? `198.51.100.${Math.floor(Math.random() * 200 + 10)}`
          : `192.168.1.${Math.floor(Math.random() * 150 + 20)}`,
        method: isAttack && randomThreat !== 'Path Traversal' ? 'POST' : 'GET',
        path: chosenEndpoint,
        action: isAttack ? 'BLOCK' : 'ALLOW',
        threat_type: isAttack ? randomThreat : 'Normal',
        risk_level: isAttack ? (Math.random() > 0.5 ? 'CRITICAL' : 'HIGH') : 'LOW',
        anomaly_score: isAttack
          ? +(0.75 + Math.random() * 0.22).toFixed(3)
          : +(0.02 + Math.random() * 0.05).toFixed(3),
        threat_confidence: isAttack
          ? +(0.92 + Math.random() * 0.07).toFixed(3)
          : 0.998,
        block_reason: isAttack ? 'ML_THREAT_DETECTED' : null,
        ml_latency_ms: +(2.8 + Math.random() * 1.8).toFixed(1),
        total_latency_ms: +(4.5 + Math.random() * 3.0).toFixed(1),
        body: isAttack
          ? randomThreat === 'SQLi'
            ? "{\"username\":\"admin' OR '1'='1' --\",\"password\":\"guess\"}"
            : randomThreat === 'XSS'
            ? '{"rating":5,"comment":"<script>alert(1)</script>"}'
            : randomThreat === 'Command Injection'
            ? '{"host":"127.0.0.1; whoami"}'
            : ''
          : '',
        attack_payload_highlight: isAttack
          ? randomThreat === 'SQLi'
            ? "' OR '1'='1' --"
            : randomThreat === 'XSS'
            ? '<script>alert(1)</script>'
            : randomThreat === 'Command Injection'
            ? '; whoami'
            : '../../../../etc/passwd'
          : null,
      };

      localStore.recordSimulatedVerdict(newVerdict);
      setVerdicts((prev) => [newVerdict, ...prev.slice(0, 99)]);
      setStats({ ...localStore.stats });
      setBlockedIps([...localStore.blockedIps]);
    }, 2800);

    return () => clearInterval(streamInterval);
  }, [isStreaming]);

  const handleTestPayload = () => {
    const isSqli = testBody.includes("' OR '1'='1'") || testUrl.includes("'");
    const isXss = testBody.includes('<script') || testUrl.includes('<script');
    const isPath = testUrl.includes('..');

    let threat_type = 'Normal';
    let risk_level = 'LOW';
    let anomaly_score = 0.038;
    let confidence = 0.996;

    if (isSqli) {
      threat_type = 'SQLi';
      risk_level = 'CRITICAL';
      anomaly_score = 0.932;
      confidence = 0.985;
    } else if (isXss) {
      threat_type = 'XSS';
      risk_level = 'HIGH';
      anomaly_score = 0.812;
      confidence = 0.945;
    } else if (isPath) {
      threat_type = 'Path Traversal';
      risk_level = 'CRITICAL';
      anomaly_score = 0.915;
      confidence = 0.978;
    }

    setTestResult({
      threat_type,
      risk_level,
      anomaly_score,
      confidence,
      features: {
        num_sql_keywords: isSqli ? 4.2 : 0,
        num_special_chars: isSqli || isXss ? 3.8 : 0.4,
        num_xss_keywords: isXss ? 5.1 : 0,
        num_path_traversal_patterns: isPath ? 5.6 : 0,
        payload_entropy: +(3.2 + Math.random() * 1.2).toFixed(2),
        url_length: testUrl.length,
      },
    });
  };

  return (
    <div className="hub-layout">
      {/* Left Sidebar matching SchoolHub template */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        blockedCount={blockedIps.length}
      />

      {/* Main Content Area */}
      <main className="hub-main">
        {/* Top Search & User Chip Header */}
        <Header
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          isStreaming={isStreaming}
          setIsStreaming={setIsStreaming}
          onRefresh={refreshTelemetry}
          isLive={isLive}
        />

        {/* 1. DASHBOARD VIEW (Exact match to screenshot template) */}
        {activeTab === 'dashboard' && (
          <>
            {/* 4 Pastel Top Cards: Purple, Yellow, Blue, Orange */}
            <KpiCards stats={stats} />

            {/* Content Split: Left Charts & Table + Right Calendar Column */}
            <div className="hub-content-split">
              {/* Left Column: Donut + Attendance + Table */}
              <div>
                <div className="hub-charts-row">
                  {/* Concentric Double-Ring Donut Card */}
                  <DonutChartCard verdicts={verdicts} />

                  {/* Attendance Multi-Bar Chart with 95% Tooltip */}
                  <AttendanceChartCard />
                </div>

                {/* Real-time Threat Stream Table */}
                <VerdictFeed
                  verdicts={verdicts}
                  onSelectVerdict={(v) => setSelectedVerdict(v)}
                  searchFilter={searchQuery}
                />
              </div>

              {/* Right Column: Calendar Strip + Agenda + Messages */}
              <div className="right-column-stack">
                <CalendarStrip />
                <AgendaAlertsCard
                  onSelectAlert={(title) => {
                    const match = verdicts.find((v) => v.action === 'BLOCK');
                    if (match) setSelectedVerdict(match);
                  }}
                />
                <RecentMessagesCard
                  verdicts={verdicts}
                  onSelectVerdict={(v) => setSelectedVerdict(v)}
                  onViewAll={() => setActiveTab('verdicts')}
                />
              </div>
            </div>
          </>
        )}

        {/* 2. ATTACK STUDIO VIEW */}
        {activeTab === 'simulator' && (
          <AttackSimulatorPanel
            onNewVerdictRecorded={(v) => {
              setVerdicts((prev) => [v, ...prev]);
              refreshTelemetry();
            }}
          />
        )}

        {/* 3. LIVE STREAM VIEW */}
        {activeTab === 'verdicts' && (
          <VerdictFeed
            verdicts={verdicts}
            onSelectVerdict={(v) => setSelectedVerdict(v)}
            searchFilter={searchQuery}
          />
        )}

        {/* 4. EXPLAINABLE AI VIEW */}
        {activeTab === 'xai' && (
          <div className="white-card">
            <div className="card-header-row">
              <div>
                <h3 className="card-title">Explainable AI (XAI) Model Architecture & Features</h3>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Deep Autoencoder 0.280 Threshold • Hybrid CNN+BiLSTM Classification • 18-Feature Vector
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
                Live Neural Feature Extraction & Inference Sandbox
              </h4>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Test any custom HTTP URL and payload to observe real-time feature extraction and prediction.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Target Endpoint
                  </label>
                  <input
                    type="text"
                    value={testUrl}
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
                    onChange={(e) => setTestBody(e.target.value)}
                    className="hub-search-input font-mono"
                    style={{ width: '100%', paddingLeft: '1rem' }}
                  />
                </div>
              </div>

              <button className="hub-btn-primary" onClick={handleTestPayload}>
                <span>Run Neural Inference</span>
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
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: testResult.risk_level === 'CRITICAL' ? '#fee2e2' : '#fef3c7',
                        color: testResult.risk_level === 'CRITICAL' ? '#dc2626' : '#d97706',
                      }}
                    >
                      {testResult.risk_level}
                    </span>
                    <strong style={{ fontSize: '0.85rem' }}>
                      Predicted: {testResult.threat_type} ({(testResult.confidence * 100).toFixed(1)}% confidence)
                    </strong>
                    <span className="font-mono" style={{ fontSize: '0.76rem', color: '#16a34a' }}>
                      Reconstruction Error: {testResult.anomaly_score}
                    </span>
                  </div>

                  <pre style={{ background: '#0f172a', color: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                    {JSON.stringify(testResult.features, null, 2)}
                  </pre>
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
          />
        )}

        {/* 6. VICTIM STOREFRONT VIEW */}
        {activeTab === 'victim' && <StorefrontPreview />}

        {/* 7. SYSTEM TOPOLOGY VIEW */}
        {activeTab === 'topology' && <TopologyMap />}

        {/* 8. PROFILE / SETTINGS VIEW */}
        {(activeTab === 'profile' || activeTab === 'settings') && (
          <div className="white-card">
            <h3 className="card-title">Security Gateway Configuration</h3>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.25rem', marginBottom: '1rem' }}>
              Perimeter policy, rate limits, and risk thresholds
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Rate Limit Window</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '2px' }}>60 Seconds (100 req max)</div>
              </div>
              <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Blocklist TTL</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '2px' }}>3600 Seconds (1 Hour)</div>
              </div>
              <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Auto-Block Threshold</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '2px' }}>CRITICAL & HIGH</div>
              </div>
            </div>
          </div>
        )}
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
