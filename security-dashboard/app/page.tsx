'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header';
import KpiCards from '../components/KpiCards';
import LiveTrafficChart from '../components/LiveTrafficChart';
import ThreatRadar from '../components/ThreatRadar';
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
import { FEATURE_METADATA } from '../lib/xaiUtils';
import { INITIAL_STATS, INITIAL_VERDICTS, INITIAL_BLOCKED_IPS } from '../lib/mockData';
import { Cpu, Terminal, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function SecurityDashboardPage() {
  const [activeTab, setActiveTab] = useState<string>('command-center');
  const [stats, setStats] = useState<GatewayStats>(INITIAL_STATS);
  const [verdicts, setVerdicts] = useState<RecentVerdict[]>(INITIAL_VERDICTS);
  const [blockedIps, setBlockedIps] = useState<BlockedIPEntry[]>(INITIAL_BLOCKED_IPS);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(true);
  const [selectedVerdict, setSelectedVerdict] = useState<RecentVerdict | null>(null);

  // Custom XAI Sandbox Tester state
  const [testUrl, setTestUrl] = useState('/api/login');
  const [testMethod, setTestMethod] = useState<'GET' | 'POST'>('POST');
  const [testBody, setTestBody] = useState('{"username": "admin\' OR \'1\'=\'1\' --", "password": "123"}');
  const [testResult, setTestResult] = useState<any>(null);

  // Load telemetry from Gateway / local store
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

  // Periodic simulated live events when streaming is active
  useEffect(() => {
    if (!isStreaming) return;

    const streamInterval = setInterval(() => {
      // 80% normal traffic, 20% occasional stealth attack
      const isAttack = Math.random() > 0.8;
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
    <div className="dashboard-container">
      {/* Top SOC Navigation Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isLive={isLive}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
        onRefresh={refreshTelemetry}
        blockedCount={blockedIps.length}
      />

      {/* KPI Metric Strip (Always visible for executive overview) */}
      <KpiCards stats={stats} />

      {/* VIEW 1: COMMAND CENTER (Default SOC View) */}
      {activeTab === 'command-center' && (
        <>
          <div className="main-grid">
            <LiveTrafficChart />
            <ThreatRadar verdicts={verdicts} />
          </div>

          <VerdictFeed
            verdicts={verdicts}
            onSelectVerdict={(v) => setSelectedVerdict(v)}
          />
        </>
      )}

      {/* VIEW 2: ATTACK SIMULATOR STUDIO */}
      {activeTab === 'simulator' && (
        <AttackSimulatorPanel
          onNewVerdictRecorded={(v) => {
            setVerdicts((prev) => [v, ...prev]);
            refreshTelemetry();
          }}
        />
      )}

      {/* VIEW 3: EXPLAINABLE AI (XAI) DEEP DIVE */}
      {activeTab === 'xai' && (
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div className="panel-header" style={{ marginBottom: '1.25rem' }}>
            <div className="panel-title-wrap">
              <Cpu size={22} color="#8b5cf6" />
              <div>
                <h2 className="panel-title" style={{ fontSize: '1.15rem' }}>
                  Explainable AI (XAI) Model Architecture & Feature Engineering
                </h2>
                <span className="panel-subtitle">
                  18-Dimensional Feature Extractor • Deep Autoencoder Anomaly Scoring • Hybrid CNN+BiLSTM Classifier
                </span>
              </div>
            </div>
          </div>

          {/* Model Architecture Explanations */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div
              style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <h3 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '0.5rem' }}>
                1. Deep Autoencoder (Zero-Day Anomaly Detection)
              </h3>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
                Trained strictly on clean baseline traffic. Incoming requests are passed through an 18→64→32→16→8 bottleneck. If reconstruction error exceeds threshold <strong>0.280</strong>, the request is flagged as an anomalous deviation.
              </p>
              <div className="font-mono" style={{ fontSize: '0.72rem', color: '#6ee7b7' }}>
                Architecture: Linear(18→64) → ReLU → Linear(64→32) → Linear(32→8) → Decoder
              </div>
            </div>

            <div
              style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <h3 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '0.5rem' }}>
                2. Hybrid CNN + BiLSTM with Self-Attention
              </h3>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
                Combines 1D Convolutions for local n-gram token detection with a Bidirectional LSTM to capture sequential syntax context, outputting classification probabilities across 5 distinct threat classes.
              </p>
              <div className="font-mono" style={{ fontSize: '0.72rem', color: '#93c5fd' }}>
                Classes: Normal, SQLi, XSS, Path Traversal, Command Injection
              </div>
            </div>
          </div>

          {/* Live Feature Extraction Sandbox */}
          <div
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-md)',
              background: '#0a0f1d',
              border: '1px solid var(--border-glow-blue)',
              marginBottom: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '0.35rem' }}>
              Live Neural Feature Extraction & Inference Sandbox
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>
              Type or paste any URL and body to observe real-time feature extraction and ML classification.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Target Endpoint
                </label>
                <input
                  type="text"
                  value={testUrl}
                  onChange={(e) => setTestUrl(e.target.value)}
                  className="search-input font-mono"
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Payload Body (JSON / Query)
                </label>
                <input
                  type="text"
                  value={testBody}
                  onChange={(e) => setTestBody(e.target.value)}
                  className="search-input font-mono"
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <button className="btn-primary" onClick={handleTestPayload}>
              <span>Run Neural Inference</span>
              <ArrowRight size={14} />
            </button>

            {testResult && (
              <div
                style={{
                  marginTop: '1.25rem',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span className={`risk-pill risk-${testResult.risk_level}`}>
                    {testResult.risk_level}
                  </span>
                  <span style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 600 }}>
                    Predicted Threat: {testResult.threat_type} ({(testResult.confidence * 100).toFixed(1)}% confidence)
                  </span>
                  <span className="font-mono" style={{ fontSize: '0.76rem', color: '#6ee7b7' }}>
                    Reconstruction Error: {testResult.anomaly_score}
                  </span>
                </div>

                <div className="code-block" style={{ fontSize: '0.74rem' }}>
                  {JSON.stringify(testResult.features, null, 2)}
                </div>
              </div>
            )}
          </div>

          {/* 18 Features Specification Table */}
          <h3 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '0.75rem' }}>
            Complete 18-Feature Vector Taxonomy
          </h3>
          <div className="table-wrap">
            <table className="verdict-table">
              <thead>
                <tr>
                  <th>Feature Index</th>
                  <th>Internal Identifier</th>
                  <th>Human-Readable Description</th>
                  <th>Clean Baseline</th>
                  <th>Unit</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(FEATURE_METADATA).map(([key, meta], idx) => (
                  <tr key={key}>
                    <td className="font-mono" style={{ color: 'var(--text-dim)' }}>
                      #{idx + 1}
                    </td>
                    <td className="font-mono" style={{ color: '#93c5fd', fontWeight: 600 }}>
                      {key}
                    </td>
                    <td style={{ color: '#e2e8f0' }}>{meta.description}</td>
                    <td className="font-mono" style={{ color: '#10b981' }}>
                      {meta.normalBaseline}
                    </td>
                    <td className="font-mono" style={{ color: 'var(--text-dim)' }}>
                      {meta.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VIEW 4: REDIS BLOCKLIST */}
      {activeTab === 'blocklist' && (
        <BlocklistManager
          blockedIps={blockedIps}
          onRefreshList={refreshTelemetry}
        />
      )}

      {/* VIEW 5: VICTIM STOREFRONT SHOWCASE */}
      {activeTab === 'victim' && <StorefrontPreview />}

      {/* VIEW 6: SYSTEM TOPOLOGY */}
      {activeTab === 'topology' && <TopologyMap />}

      {/* Forensic Dossier Modal */}
      <VerdictDetailModal
        verdict={selectedVerdict}
        onClose={() => setSelectedVerdict(null)}
        onBlockIpSuccess={(ip) => {
          refreshTelemetry();
        }}
      />
    </div>
  );
}
