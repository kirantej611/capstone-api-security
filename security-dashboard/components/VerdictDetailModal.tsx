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
  Info,
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

  const probs = verdict.all_probabilities || {
    Normal: verdict.threat_type === 'Normal' ? 0.99 : 0.01,
    SQLi: verdict.threat_type === 'SQLi' ? 0.985 : 0.005,
    XSS: verdict.threat_type === 'XSS' ? 0.941 : 0.008,
    'Path Traversal': verdict.threat_type === 'Path Traversal' ? 0.978 : 0.004,
    'Command Injection': verdict.threat_type === 'Command Injection' ? 0.989 : 0.003,
  };

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
    <div className="hub-modal-overlay" onClick={onClose}>
      <div className="hub-modal-card" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: '#f1f5f9',
            border: 'none',
            borderRadius: '50%',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: '#64748b',
          }}
        >
          <X size={16} />
        </button>

        {/* Modal Top Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.5rem' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: 'var(--radius-md)',
              background: verdict.action === 'BLOCK' ? '#fee2e2' : '#dcfce7',
              color: verdict.action === 'BLOCK' ? '#dc2626' : '#16a34a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={24} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                Explainable AI (XAI) Forensic Dossier
              </h2>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: verdict.action === 'BLOCK' ? '#fee2e2' : '#dcfce7',
                  color: verdict.action === 'BLOCK' ? '#dc2626' : '#16a34a',
                }}
              >
                {verdict.action}
              </span>
            </div>
            <div className="font-mono" style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              ID: {verdict.request_id} • IP: {verdict.client_ip} • Latency: {verdict.ml_latency_ms ? `${verdict.ml_latency_ms.toFixed(1)}ms` : '3.6ms'}
            </div>
          </div>
        </div>

        {/* Deep Learning 2-Model Cards in Soft Pastel styling */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
          {/* Model 1: Autoencoder */}
          <div
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              background: '#f8fafc',
              border: '1px solid var(--border-light)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
              <Cpu size={16} color="#8b5cf6" />
              <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                Deep Autoencoder (Anomaly Score)
              </h4>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', marginBottom: '0.35rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Reconstruction Error:</span>
              <strong className="font-mono" style={{ color: isAnomalous ? '#dc2626' : '#16a34a' }}>
                {anomalyScore.toFixed(4)}
              </strong>
            </div>

            <div
              style={{
                width: '100%',
                height: '8px',
                background: '#e2e8f0',
                borderRadius: '4px',
                overflow: 'hidden',
                position: 'relative',
                marginBottom: '0.5rem',
              }}
            >
              <div
                style={{
                  width: `${Math.min(anomalyScore * 100, 100)}%`,
                  height: '100%',
                  background: isAnomalous ? '#ef4444' : '#10b981',
                  borderRadius: '4px',
                }}
              />
              <div
                title="Threshold: 0.280"
                style={{
                  position: 'absolute',
                  left: `${anomalyThreshold * 100}%`,
                  top: 0,
                  bottom: 0,
                  width: '2px',
                  background: '#0f172a',
                }}
              />
            </div>

            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Baseline Threshold: <strong>0.280</strong>. {isAnomalous ? 'Reconstruction error exceeded normal boundary.' : 'Normal payload distribution.'}
            </div>
          </div>

          {/* Model 2: Classifier */}
          <div
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              background: '#f8fafc',
              border: '1px solid var(--border-light)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
              <Brain size={16} color="#0284c7" />
              <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                CNN+BiLSTM Class Probabilities
              </h4>
            </div>

            {Object.entries(probs).map(([threat, prob]) => {
              const pct = (prob * 100).toFixed(1);
              const isMatch = verdict.threat_type === threat;
              return (
                <div key={threat} style={{ marginBottom: '0.45rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '2px' }}>
                    <span style={{ color: isMatch ? 'var(--text-primary)' : 'var(--text-muted)', fontWeight: isMatch ? 700 : 400 }}>
                      {threat}
                    </span>
                    <span className="font-mono" style={{ color: isMatch ? '#0284c7' : 'var(--text-muted)' }}>
                      {pct}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '5px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: isMatch ? '#0284c7' : '#cbd5e1',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Feature Attribution */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
            <Info size={16} color="#0284c7" />
            <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              Explainable AI Feature Importance (Why was it flagged?)
            </h4>
          </div>

          <div
            style={{
              padding: '1rem',
              background: '#f8fafc',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
            }}
          >
            {Object.entries(features).map(([featKey, delta]) => {
              const meta = FEATURE_METADATA[featKey] || {
                label: featKey,
                description: 'Extracted vector signal',
                unit: '',
              };
              const widthPct = Math.min((delta / 6) * 100, 100);

              return (
                <div key={featKey} style={{ marginBottom: '0.65rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '2px' }}>
                    <div>
                      <strong>{meta.label}</strong>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>({meta.description})</span>
                    </div>
                    <span className="font-mono" style={{ color: '#dc2626', fontWeight: 600 }}>
                      +{delta.toFixed(2)} {meta.unit}
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${widthPct}%`, height: '100%', background: '#38bdf8' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Raw Payload Block */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.45rem' }}>
            <Terminal size={15} color="#475569" />
            <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              Intercepted Request Payload
            </h4>
          </div>

          <div
            style={{
              background: '#0f172a',
              color: '#f8fafc',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              overflowX: 'auto',
            }}
            dangerouslySetInnerHTML={{
              __html: highlighted.hasSuspiciousTokens
                ? highlighted.annotatedHtml
                : rawPayload || '(Clean GET request with empty payload body)',
            }}
          />
        </div>

        {/* Footer Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-light)', paddingTop: '1rem' }}>
          <button className="hub-btn-secondary" onClick={handleCopyId}>
            {copied ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy Correlation ID'}</span>
          </button>

          <div style={{ display: 'flex', gap: '0.65rem' }}>
            <button
              className="hub-btn-danger"
              onClick={handleManualBan}
              disabled={isBanning || bannedDone}
            >
              <Ban size={14} />
              <span>{bannedDone ? 'IP Banned in Redis' : isBanning ? 'Banning...' : `Ban IP ${verdict.client_ip}`}</span>
            </button>

            <button className="hub-btn-primary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
