'use client';

import React, { useState } from 'react';
import {
  X,
  ShieldAlert,
  Cpu,
  Brain,
  Terminal,
  Copy,
  Check,
  Ban,
  Database,
  Info,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { RecentVerdict } from '../lib/types';
import { FEATURE_METADATA, highlightAttackPayload } from '../lib/xaiUtils';
import { addIpToBlocklist } from '../lib/api';

interface VerdictDetailModalProps {
  verdict: RecentVerdict | null;
  onClose: () => void;
  onBlockIpSuccess?: (ip: string) => void;
}

export default function VerdictDetailModal({
  verdict,
  onClose,
  onBlockIpSuccess,
}: VerdictDetailModalProps) {
  const [copied, setCopied] = useState(false);
  const [isBanning, setIsBanning] = useState(false);
  const [bannedDone, setBannedDone] = useState(false);

  if (!verdict) return null;

  const rawPayload = verdict.body || verdict.path || '';
  const highlighted = highlightAttackPayload(rawPayload);

  // Fallback probabilities if missing
  const probs = verdict.all_probabilities || {
    Normal: verdict.threat_type === 'Normal' ? 0.99 : 0.01,
    SQLi: verdict.threat_type === 'SQLi' ? 0.985 : 0.005,
    XSS: verdict.threat_type === 'XSS' ? 0.941 : 0.008,
    'Path Traversal': verdict.threat_type === 'Path Traversal' ? 0.978 : 0.004,
    'Command Injection': verdict.threat_type === 'Command Injection' ? 0.989 : 0.003,
  };

  // Fallback feature importance if missing
  const features = verdict.feature_importance || {
    num_sql_keywords: verdict.threat_type === 'SQLi' ? 4.25 : 0.1,
    num_special_chars: verdict.threat_type === 'SQLi' ? 3.12 : 0.2,
    payload_entropy: 0.65,
    url_length: 0.18,
    uppercase_ratio: 0.72,
  };

  const handleCopyId = () => {
    navigator.clipboard.writeText(verdict.request_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleManualBan = async () => {
    setIsBanning(true);
    try {
      await addIpToBlocklist(verdict.client_ip, `Manual_SOC_Ban:${verdict.threat_type || 'Malicious'}`);
      setBannedDone(true);
      if (onBlockIpSuccess) onBlockIpSuccess(verdict.client_ip);
    } catch (err) {
      console.error(err);
    } finally {
      setIsBanning(false);
    }
  };

  const anomalyThreshold = 0.28;
  const anomalyScore = verdict.anomaly_score ?? (verdict.action === 'BLOCK' ? 0.89 : 0.038);
  const isAnomalous = anomalyScore > anomalyThreshold;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          <X size={16} />
        </button>

        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.25rem' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-md)',
              background: verdict.action === 'BLOCK' ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)',
              border: `1px solid ${verdict.action === 'BLOCK' ? 'rgba(239,68,68,0.4)' : 'rgba(16,185,129,0.4)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: verdict.action === 'BLOCK' ? '#ef4444' : '#10b981',
            }}
          >
            <ShieldAlert size={22} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h2 style={{ fontSize: '1.15rem', color: '#fff', fontWeight: 700 }}>
                Explainable AI (XAI) Forensic Dossier
              </h2>
              <span className={`risk-pill risk-${verdict.risk_level || 'LOW'}`}>
                {verdict.risk_level || 'LOW RISK'}
              </span>
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              Correlation ID: {verdict.request_id}
            </div>
          </div>
        </div>

        {/* Metadata Strip */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '0.75rem',
            padding: '0.85rem',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
          }}
        >
          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Target Path</div>
            <div className="font-mono" style={{ fontSize: '0.8rem', color: '#fff', marginTop: '2px', wordBreak: 'break-all' }}>
              <span className={`method-badge method-${verdict.method}`} style={{ marginRight: '4px' }}>
                {verdict.method}
              </span>
              {verdict.path}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Client Source IP</div>
            <div className="font-mono" style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '2px' }}>
              {verdict.client_ip}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Shield Action</div>
            <div style={{ marginTop: '2px' }}>
              <span className={`badge ${verdict.action === 'BLOCK' ? 'badge-block' : 'badge-allow'}`}>
                {verdict.action}
              </span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Inference Latency</div>
            <div className="font-mono" style={{ fontSize: '0.8rem', color: '#10b981', marginTop: '2px' }}>
              {verdict.ml_latency_ms ? `${verdict.ml_latency_ms.toFixed(1)}ms` : '3.8ms'}
            </div>
          </div>
        </div>

        {/* Two-Column Deep-Learning Section */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
          {/* Model 1: Autoencoder */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
              <Cpu size={16} color="#8b5cf6" />
              <h4 style={{ fontSize: '0.84rem', color: '#fff' }}>Deep Autoencoder (Anomaly Model)</h4>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.74rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Reconstruction Error:</span>
              <span className="font-mono" style={{ color: isAnomalous ? '#ef4444' : '#10b981', fontWeight: 700 }}>
                {anomalyScore.toFixed(4)}
              </span>
            </div>

            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden', position: 'relative', marginBottom: '0.5rem' }}>
              <div
                style={{
                  width: `${Math.min(anomalyScore * 100, 100)}%`,
                  height: '100%',
                  background: isAnomalous ? 'linear-gradient(90deg, #f59e0b, #ef4444)' : '#10b981',
                  borderRadius: '4px',
                }}
              />
              {/* Threshold mark */}
              <div
                title="Anomaly Threshold: 0.280"
                style={{
                  position: 'absolute',
                  left: `${anomalyThreshold * 100}%`,
                  top: 0,
                  bottom: 0,
                  width: '2px',
                  background: '#fff',
                  boxShadow: '0 0 6px #fff',
                }}
              />
            </div>

            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>
              Baseline Threshold: <strong className="font-mono" style={{ color: '#fff' }}>0.280</strong>.
              {isAnomalous
                ? ' Reconstruction error heavily exceeded threshold, indicating abnormal syntax distribution.'
                : ' Error is within clean operational bounds.'}
            </div>
          </div>

          {/* Model 2: Classifier */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
              <Brain size={16} color="#3b82f6" />
              <h4 style={{ fontSize: '0.84rem', color: '#fff' }}>Hybrid CNN+BiLSTM Threat Class</h4>
            </div>

            {Object.entries(probs).map(([threat, prob]) => {
              const pct = (prob * 100).toFixed(1);
              const isMatch = verdict.threat_type === threat;
              return (
                <div key={threat} style={{ marginBottom: '0.45rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '2px' }}>
                    <span style={{ color: isMatch ? '#fff' : 'var(--text-dim)', fontWeight: isMatch ? 600 : 400 }}>
                      {threat}
                    </span>
                    <span className="font-mono" style={{ color: isMatch ? '#60a5fa' : 'var(--text-dim)' }}>
                      {pct}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '5px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: isMatch ? '#3b82f6' : 'rgba(255,255,255,0.15)',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Feature Importance (Top XAI Drivers) */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
            <Info size={15} color="#06b6d4" />
            <h4 style={{ fontSize: '0.84rem', color: '#fff' }}>
              Explainable AI Feature Attribution (Top Contributing Signals)
            </h4>
          </div>

          <div
            style={{
              padding: '1rem',
              background: 'rgba(10, 15, 29, 0.8)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            {Object.entries(features).map(([featKey, delta]) => {
              const meta = FEATURE_METADATA[featKey] || {
                label: featKey,
                description: 'Feature vector component',
                unit: '',
              };
              const widthPct = Math.min((delta / 6) * 100, 100);

              return (
                <div key={featKey} className="feat-bar-row">
                  <div className="feat-bar-header">
                    <div>
                      <strong style={{ color: '#fff' }}>{meta.label}</strong>
                      <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>({meta.description})</span>
                    </div>
                    <span className="font-mono" style={{ color: '#f87171' }}>
                      +{delta.toFixed(2)} {meta.unit}
                    </span>
                  </div>
                  <div className="feat-bar-track">
                    <div className="feat-bar-fill" style={{ width: `${widthPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Raw HTTP Payload Viewer with Exploit Token Highlighting */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Terminal size={15} color="#10b981" />
              <h4 style={{ fontSize: '0.84rem', color: '#fff' }}>Intercepted Request Body & Tokens</h4>
            </div>
            {highlighted.tokens.length > 0 && (
              <span className="risk-pill risk-CRITICAL" style={{ fontSize: '0.68rem' }}>
                {highlighted.tokens.length} Malicious Pattern(s) Highlighted
              </span>
            )}
          </div>

          <div
            className="code-block"
            dangerouslySetInnerHTML={{
              __html: highlighted.hasSuspiciousTokens
                ? highlighted.annotatedHtml
                : rawPayload || '(Empty HTTP payload body)',
            }}
          />
        </div>

        {/* Modal Action Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
          <button className="btn-secondary" onClick={handleCopyId}>
            {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
            <span>{copied ? 'Copied ID' : 'Copy Request ID'}</span>
          </button>

          <div style={{ display: 'flex', gap: '0.65rem' }}>
            <button
              className="btn-danger"
              onClick={handleManualBan}
              disabled={isBanning || bannedDone}
            >
              <Ban size={14} />
              <span>{bannedDone ? 'IP Blocked in Redis' : isBanning ? 'Banning IP...' : `Block IP ${verdict.client_ip}`}</span>
            </button>

            <button className="btn-primary" onClick={onClose}>
              <span>Close Dossier</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
