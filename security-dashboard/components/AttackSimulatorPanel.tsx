'use client';

import React, { useState } from 'react';
import {
  Zap,
  Shield,
  Flame,
  CheckCircle,
  AlertTriangle,
  Clock,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { ATTACK_SCENARIOS } from '../lib/xaiUtils';
import { executeSimulatedRequest } from '../lib/api';
import { AttackScenario, RecentVerdict } from '../lib/types';

interface AttackSimulatorPanelProps {
  onNewVerdictRecorded?: (verdict: RecentVerdict) => void;
}

export default function AttackSimulatorPanel({
  onNewVerdictRecorded,
}: AttackSimulatorPanelProps) {
  const [selectedScenario, setSelectedScenario] = useState<AttackScenario>(ATTACK_SCENARIOS[0]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<{
    scenario: AttackScenario;
    mode: 'SHIELD' | 'UNPROTECTED';
    statusCode: number;
    latencyMs: number;
    body: any;
    timestamp: string;
  } | null>(null);

  const [narrativeRunning, setNarrativeRunning] = useState<boolean>(false);
  const [narrativeStep, setNarrativeStep] = useState<string>('');

  const runAttack = async (scenario: AttackScenario, useShield: boolean) => {
    setIsRunning(true);
    try {
      const res = await executeSimulatedRequest(
        scenario.targetEndpoint,
        scenario.method,
        scenario.payload,
        useShield
      );

      const result = {
        scenario,
        mode: useShield ? ('SHIELD' as const) : ('UNPROTECTED' as const),
        statusCode: res.statusCode,
        latencyMs: res.latencyMs,
        body: res.body,
        timestamp: new Date().toLocaleTimeString(),
      };

      setLastResult(result);

      if (res.verdict && onNewVerdictRecorded) {
        onNewVerdictRecorded(res.verdict);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsRunning(false);
    }
  };

  const runAutomatedPresentation = async () => {
    setNarrativeRunning(true);
    const sequence = [
      { id: 'normal-customer-flow', text: '1/4: Simulating clean legitimate customer traffic...' },
      { id: 'sqli-auth-bypass', text: '2/4: Simulating SQL Injection auth bypass on /api/login...' },
      { id: 'xss-product-review', text: '3/4: Simulating Stored XSS cookie stealer injection...' },
      { id: 'credential-stuffing-burst', text: '4/4: Simulating rapid credential stuffing burst...' },
    ];

    for (const step of sequence) {
      setNarrativeStep(step.text);
      const sc = ATTACK_SCENARIOS.find((s) => s.id === step.id);
      if (sc) {
        setSelectedScenario(sc);
        await runAttack(sc, true);
        await new Promise((r) => setTimeout(r, 2000));
      }
    }

    setNarrativeStep('Automated Demo Completed! All attacks neutralized.');
    setTimeout(() => {
      setNarrativeRunning(false);
      setNarrativeStep('');
    }, 2500);
  };

  return (
    <div className="white-card">
      <div className="card-header-row" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 className="card-title">Attack Simulation Studio & Demo Suite</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Compare Protected with AI Shield (:8080) vs Direct Unprotected Victim (:8081)
          </span>
        </div>

        <button
          className="hub-btn-primary"
          onClick={runAutomatedPresentation}
          disabled={isRunning || narrativeRunning}
        >
          <Sparkles size={14} />
          <span>{narrativeRunning ? narrativeStep : 'Run 30s Executive Demo Narrative'}</span>
        </button>
      </div>

      {/* Scenario Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
        {ATTACK_SCENARIOS.map((sc) => {
          const isSelected = selectedScenario.id === sc.id;
          return (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc)}
              style={{
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                background: isSelected ? 'var(--accent-cyan-light)' : '#f8fafc',
                border: `1px solid ${isSelected ? '#38bdf8' : 'var(--border-light)'}`,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.15s ease',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {sc.title}
                  </h4>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: sc.severity === 'CRITICAL' ? '#fee2e2' : '#fef3c7',
                      color: sc.severity === 'CRITICAL' ? '#dc2626' : '#d97706',
                    }}
                  >
                    {sc.severity}
                  </span>
                </div>

                <div className="font-mono" style={{ fontSize: '0.72rem', color: '#0284c7', marginBottom: '0.5rem' }}>
                  {sc.method} {sc.targetEndpoint}
                </div>

                <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {sc.description}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button
                  className="hub-btn-primary"
                  style={{ flex: 1, padding: '0.4rem 0.6rem', fontSize: '0.75rem', justifyContent: 'center' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedScenario(sc);
                    runAttack(sc, true);
                  }}
                  disabled={isRunning}
                >
                  <Shield size={13} />
                  <span>With Shield</span>
                </button>

                <button
                  className="hub-btn-danger"
                  style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', justifyContent: 'center' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedScenario(sc);
                    runAttack(sc, false);
                  }}
                  disabled={isRunning}
                >
                  <Flame size={13} />
                  <span>Direct</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Response Telemetry Callout */}
      {lastResult && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1.25rem',
            borderRadius: 'var(--radius-lg)',
            background: '#ffffff',
            border: `1px solid ${
              lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                ? '#10b981'
                : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal'
                ? '#ef4444'
                : '#0284c7'
            }`,
            boxShadow: '0 4px 15px rgba(0,0,0,0.04)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Terminal size={17} color="#0284c7" />
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                {lastResult.scenario.title} — {lastResult.mode === 'SHIELD' ? 'Protected by AI Shield (:8080)' : 'Direct to Vulnerable Victim (:8081)'}
              </strong>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <span className="font-mono" style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <Clock size={12} style={{ display: 'inline', marginRight: '3px' }} />
                {lastResult.latencyMs}ms
              </span>
              <span
                style={{
                  fontSize: '0.76rem',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: '999px',
                  background: lastResult.statusCode === 403 ? '#fee2e2' : '#dcfce7',
                  color: lastResult.statusCode === 403 ? '#dc2626' : '#16a34a',
                }}
              >
                HTTP {lastResult.statusCode}
              </span>
            </div>
          </div>

          <div
            style={{
              padding: '0.85rem',
              borderRadius: 'var(--radius-md)',
              background:
                lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                  ? '#ecfdf5'
                  : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal'
                  ? '#fef2f2'
                  : '#f0f9ff',
              marginBottom: '0.85rem',
              fontSize: '0.76rem',
              lineHeight: 1.45,
            }}
          >
            <strong>
              {lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                ? 'AI Gateway Intercepted Threat:'
                : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal'
                ? 'Security Breach Notice:'
                : 'Request Result:'}
            </strong>{' '}
            {lastResult.mode === 'SHIELD'
              ? lastResult.scenario.explanation
              : 'Without the AI Shield, backend executed unescaped query directly against PostgreSQL! Unauthorized data exposed.'}
          </div>

          <pre
            style={{
              background: '#0f172a',
              color: '#f8fafc',
              padding: '0.85rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.74rem',
              fontFamily: 'var(--font-mono)',
              overflowX: 'auto',
            }}
          >
            {typeof lastResult.body === 'object'
              ? JSON.stringify(lastResult.body, null, 2)
              : lastResult.body}
          </pre>
        </div>
      )}
    </div>
  );
}
