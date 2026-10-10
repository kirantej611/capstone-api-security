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

  const rawPayload = verdict.body || '';
  const highlighted = highlightAttackPayload(rawPayload);
  const probs = verdict.all_probabilities;
  const features = verdict.feature_importance;
  const maxFeatureMagnitude = Math.max(0, ...Object.values(features || {}).map(Math.abs));

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

  const anomalyScore = verdict.anomaly_score;

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
              ID: {verdict.request_id} • IP: {verdict.client_ip} • {verdict.method} {verdict.path} • Latency: {verdict.ml_latency_ms == null ? '—' : `${verdict.ml_latency_ms.toFixed(1)}ms`}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          {anomalyScore != null && (
            <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-lg)', background: '#f8fafc', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
                <Cpu size={16} color="#8b5cf6" />
                <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>Anomaly score</h4>
              </div>
              <strong className="font-mono">{anomalyScore.toFixed(4)}</strong>
            </div>
          )}

          {probs && Object.keys(probs).length > 0 && (
            <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-lg)', background: '#f8fafc', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
                <Brain size={16} color="#0284c7" />
                <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>Classifier probabilities</h4>
              </div>
              {Object.entries(probs).map(([threat, probability]) => {
                const pct = Math.min(Math.max(probability * 100, 0), 100);
                const isMatch = verdict.threat_type === threat;
                return (
                  <div key={threat} style={{ marginBottom: '0.45rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '2px' }}>
                      <span style={{ color: isMatch ? 'var(--text-primary)' : 'var(--text-muted)', fontWeight: isMatch ? 700 : 400 }}>{threat}</span>
                      <span className="font-mono" style={{ color: isMatch ? '#0284c7' : 'var(--text-muted)' }}>{pct.toFixed(1)}%</span>
                    </div>
                    <div style={{ width: '100%', height: '5px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: isMatch ? '#0284c7' : '#cbd5e1' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {anomalyScore == null && (!probs || Object.keys(probs).length === 0) && (
            <p className="dashboard-empty-state">This verdict does not include model scores.</p>
          )}
        </div>

        {/* Feature Attribution */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
            <Info size={16} color="#0284c7" />
            <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              Feature importance (when supplied by the model)
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
            {features && Object.keys(features).length > 0 ? Object.entries(features).map(([featKey, delta]) => {
              const meta = FEATURE_METADATA[featKey] || {
                label: featKey,
                description: 'Extracted vector signal',
                unit: '',
              };
              const widthPct = maxFeatureMagnitude > 0
                ? (Math.abs(delta) / maxFeatureMagnitude) * 100
                : 0;

              return (
                <div key={featKey} style={{ marginBottom: '0.65rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '2px' }}>
                    <div>
                      <strong>{meta.label}</strong>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>({meta.description})</span>
                    </div>
                    <span className="font-mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      {delta.toFixed(2)} {meta.unit}
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${widthPct}%`, height: '100%', background: '#38bdf8' }} />
                  </div>
                </div>
              );
            }) : <p className="dashboard-empty-state">No feature importance data was included with this verdict.</p>}
          </div>
        </div>

        {/* Raw Payload Block */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.45rem' }}>
            <Terminal size={15} color="#475569" />
            <h4 style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              Request body
            </h4>
          </div>

          <pre
            style={{
              background: '#0f172a',
              color: '#f8fafc',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              overflowX: 'auto',
              whiteSpace: 'pre-wrap',
              overflowWrap: 'anywhere',
            }}
          >
            {rawPayload
              ? highlighted.parts.map((part, index) => (
                  <span
                    key={`${index}-${part.text}`}
                    style={part.suspicious ? { background: '#7f1d1d', color: '#fecaca' } : undefined}
                  >
                    {part.text}
                  </span>
                ))
              : 'No request body was recorded for this request.'}
          </pre>
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
              <span>{bannedDone ? 'IP added to blocklist' : isBanning ? 'Adding...' : `Block IP ${verdict.client_ip}`}</span>
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
