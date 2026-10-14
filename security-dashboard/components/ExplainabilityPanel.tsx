'use client';

import { useEffect, useMemo, useState } from 'react';
import { Activity, Brain, Info, ShieldCheck } from 'lucide-react';
import { RecentVerdict } from '../lib/types';
import { MODEL_FEATURES } from '../lib/xaiUtils';
import { formatIstTimestamp } from '../lib/formatters';

interface ExplainabilityPanelProps {
  verdicts: RecentVerdict[];
  isLive: boolean;
}

function formatLabel(value: string | null | undefined): string {
  if (!value) return 'Not reported';
  return value.replaceAll('_', ' ');
}

function actionColor(action: string): string {
  if (action === 'BLOCK') return '#dc2626';
  if (action === 'RATE_LIMIT') return '#d97706';
  if (action === 'FLAG') return '#7c3aed';
  return '#16a34a';
}

export default function ExplainabilityPanel({
  verdicts,
  isLive,
}: ExplainabilityPanelProps) {
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const selectedVerdict = useMemo(
    () => verdicts.find((verdict) => verdict.request_id === selectedRequestId) ?? verdicts[0],
    [selectedRequestId, verdicts]
  );

  useEffect(() => {
    if (
      selectedRequestId &&
      !verdicts.some((verdict) => verdict.request_id === selectedRequestId)
    ) {
      setSelectedRequestId(null);
    }
  }, [selectedRequestId, verdicts]);

  const probabilities = selectedVerdict?.all_probabilities ?? {};
  const rankedProbabilities = Object.entries(probabilities).sort(
    ([, first], [, second]) => second - first
  );
  const featureImportances = Object.entries(
    selectedVerdict?.feature_importance ?? {}
  ).sort(([, first], [, second]) => second - first);
  const hasModelOutput =
    selectedVerdict?.anomaly_score != null || rankedProbabilities.length > 0;

  return (
    <section className="white-card" aria-labelledby="xai-title">
      <div className="card-header-row">
        <div>
          <h2 className="card-title" id="xai-title">Explainable AI</h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Live gateway inference outputs and the current 42-feature model input
          </span>
        </div>
        <span
          style={{
            borderRadius: 999,
            padding: '0.35rem 0.7rem',
            background: isLive ? '#dcfce7' : '#f1f5f9',
            color: isLive ? '#166534' : '#475569',
            fontSize: '0.72rem',
            fontWeight: 700,
          }}
        >
          {isLive ? 'LIVE GATEWAY' : 'GATEWAY OFFLINE'}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))',
          gap: '1rem',
          marginTop: '1rem',
        }}
      >
        <aside
          style={{
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            minWidth: 0,
          }}
        >
          <div style={{ padding: '0.9rem 1rem', borderBottom: '1px solid var(--border-light)' }}>
            <h3 style={{ fontSize: '0.88rem', fontWeight: 700, margin: 0 }}>
              Recent gateway verdicts
            </h3>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '0.3rem 0 0' }}>
              Verdicts are kept in memory; some are rejected before ML inference.
            </p>
          </div>
          {verdicts.length === 0 ? (
            <p className="dashboard-empty-state">
              {isLive
                ? 'No recent gateway verdicts are available yet. Send traffic through the gateway to inspect its actual model output.'
                : 'The gateway is offline. Model explanations will appear here when live telemetry is available.'}
            </p>
          ) : (
            <div style={{ maxHeight: 470, overflowY: 'auto' }}>
              {verdicts.map((verdict) => {
                const isSelected = selectedVerdict?.request_id === verdict.request_id;
                return (
                  <button
                    key={verdict.request_id}
                    type="button"
                    onClick={() => setSelectedRequestId(verdict.request_id)}
                    aria-pressed={isSelected}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '0.8rem 1rem',
                      border: 0,
                      borderBottom: '1px solid var(--border-light)',
                      borderLeft: isSelected ? '3px solid #0284c7' : '3px solid transparent',
                      background: isSelected ? '#f0f9ff' : '#fff',
                      cursor: 'pointer',
                      color: 'inherit',
                    }}
                  >
                    <span style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                      <strong className="font-mono" style={{ fontSize: '0.74rem' }}>
                        {verdict.method} {verdict.path}
                      </strong>
                      <span style={{ color: actionColor(verdict.action), fontSize: '0.68rem', fontWeight: 700 }}>
                        {verdict.action}
                      </span>
                    </span>
                    <span
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        gap: '0.5rem',
                        marginTop: '0.35rem',
                        color: 'var(--text-muted)',
                        fontSize: '0.69rem',
                      }}
                    >
                      <span>{formatLabel(verdict.threat_type)}</span>
                      <span>{formatIstTimestamp(verdict.timestamp)}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </aside>

        <div style={{ minWidth: 0 }}>
          {!selectedVerdict ? (
            <div className="dashboard-empty-state" style={{ border: '1px dashed var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
              Select a live verdict to see the model outputs and available attribution.
            </div>
          ) : (
            <>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.75rem',
                  padding: '1rem',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-lg)',
                  background: '#f8fafc',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {selectedVerdict.request_id} · {selectedVerdict.client_ip}
                  </div>
                  <strong style={{ display: 'block', marginTop: '0.25rem' }}>
                    {selectedVerdict.method} {selectedVerdict.path}
                  </strong>
                </div>
                <span style={{ color: actionColor(selectedVerdict.action), fontWeight: 800, fontSize: '0.8rem' }}>
                  {selectedVerdict.action} · {formatLabel(selectedVerdict.threat_type)}
                </span>
              </div>

              {!hasModelOutput ? (
                <div
                  style={{
                    display: 'flex',
                    gap: '0.7rem',
                    marginTop: '1rem',
                    padding: '1rem',
                    border: '1px solid #bae6fd',
                    borderRadius: 'var(--radius-lg)',
                    background: '#f0f9ff',
                    color: '#075985',
                  }}
                >
                  <Info size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <strong style={{ fontSize: '0.85rem' }}>No classifier explanation for this verdict</strong>
                    <p style={{ fontSize: '0.76rem', margin: '0.35rem 0 0' }}>
                      The gateway did not return model scores for this request. It may have been rejected
                      before inference{selectedVerdict.block_reason ? ` (${formatLabel(selectedVerdict.block_reason)})` : ''},
                      or the ML service may not have supplied outputs. No probability or attribution is fabricated.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(145px, 1fr))',
                      gap: '0.75rem',
                      marginTop: '1rem',
                    }}
                  >
                    <MetricCard label="Final gateway action" value={selectedVerdict.action} icon={<ShieldCheck size={17} />} />
                    <MetricCard label="Final threat label" value={formatLabel(selectedVerdict.threat_type)} icon={<Brain size={17} />} />
                    <MetricCard
                      label="Anomaly score"
                      value={selectedVerdict.anomaly_score == null ? 'Not reported' : selectedVerdict.anomaly_score.toFixed(4)}
                      icon={<Activity size={17} />}
                    />
                    <MetricCard
                      label="ML latency"
                      value={selectedVerdict.ml_latency_ms == null ? 'Not reported' : `${selectedVerdict.ml_latency_ms.toFixed(1)} ms`}
                      icon={<Activity size={17} />}
                    />
                  </div>

                  {rankedProbabilities.length > 0 && (
                    <section
                      style={{
                        marginTop: '1rem',
                        padding: '1rem',
                        border: '1px solid var(--border-light)',
                        borderRadius: 'var(--radius-lg)',
                      }}
                    >
                      <h3 style={{ fontSize: '0.9rem', margin: 0 }}>Classifier probabilities</h3>
                      <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', margin: '0.35rem 0 0.9rem' }}>
                        Classifier softmax scores before gateway policy and rule-based evidence are applied.
                        The top class can differ from the final gateway label.
                      </p>
                      {rankedProbabilities.map(([name, probability]) => {
                        const percentage = Math.max(0, Math.min(100, probability * 100));
                        const isTop = name === rankedProbabilities[0][0];
                        const isFinal = name === selectedVerdict.threat_type;
                        return (
                          <div key={name} style={{ marginBottom: '0.7rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', fontSize: '0.75rem' }}>
                              <span style={{ fontWeight: isTop || isFinal ? 700 : 400 }}>
                                {name}{isTop ? ' · top classifier score' : ''}{isFinal ? ' · final label' : ''}
                              </span>
                              <span className="font-mono">{percentage.toFixed(1)}%</span>
                            </div>
                            <div style={{ height: 6, marginTop: 4, borderRadius: 4, background: '#e2e8f0', overflow: 'hidden' }}>
                              <div style={{ width: `${percentage}%`, height: '100%', background: isFinal ? '#0284c7' : '#94a3b8' }} />
                            </div>
                          </div>
                        );
                      })}
                    </section>
                  )}

                  <section
                    style={{
                      marginTop: '1rem',
                      padding: '1rem',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-lg)',
                    }}
                  >
                    <h3 style={{ fontSize: '0.9rem', margin: 0 }}>Anomaly feature attribution</h3>
                    <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', margin: '0.35rem 0 0.9rem' }}>
                      One feature at a time is replaced with its normal reference value and the change in
                      autoencoder reconstruction error is measured. These normalized values explain anomaly
                      score sensitivity, not which features caused a specific attack class.
                    </p>
                    {featureImportances.length === 0 ? (
                      <p className="dashboard-empty-state" style={{ padding: '0.75rem 0' }}>
                        The model returned no positive feature attribution for this request.
                      </p>
                    ) : (
                      featureImportances.map(([name, importance]) => {
                        const percentage = Math.max(0, Math.min(100, importance * 100));
                        return (
                          <div key={name} style={{ marginBottom: '0.7rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', fontSize: '0.75rem' }}>
                              <span className="font-mono" style={{ fontWeight: 600 }}>{formatLabel(name)}</span>
                              <span className="font-mono">{percentage.toFixed(1)}%</span>
                            </div>
                            <div style={{ height: 6, marginTop: 4, borderRadius: 4, background: '#e2e8f0', overflow: 'hidden' }}>
                              <div style={{ width: `${percentage}%`, height: '100%', background: '#38bdf8' }} />
                            </div>
                          </div>
                        );
                      })
                    )}
                  </section>
                </>
              )}
            </>
          )}
        </div>
      </div>

      <details style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-light)', paddingTop: '1rem' }}>
        <summary style={{ cursor: 'pointer', fontSize: '0.88rem', fontWeight: 700 }}>
          Current model feature reference ({MODEL_FEATURES.length} features)
        </summary>
        <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', margin: '0.65rem 0' }}>
          Features are computed from the normalized request target, body, and selected headers. This reference
          documents model inputs; it does not claim that each feature is an attack or a causal explanation.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table className="hub-table">
            <thead>
              <tr><th>#</th><th>Feature</th><th>Current definition</th><th>Measure</th></tr>
            </thead>
            <tbody>
              {MODEL_FEATURES.map(([name, description, unit], index) => (
                <tr key={name}>
                  <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{index + 1}</td>
                  <td className="font-mono" style={{ color: '#0284c7', fontWeight: 600 }}>{name}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{description}</td>
                  <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      style={{
        minWidth: 0,
        padding: '0.85rem',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-md)',
        background: '#fff',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0284c7' }}>
        {icon}
        <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>{label}</span>
      </div>
      <div style={{ marginTop: '0.45rem', fontWeight: 700, fontSize: '0.86rem', overflowWrap: 'anywhere' }}>
        {value}
      </div>
    </div>
  );
}
