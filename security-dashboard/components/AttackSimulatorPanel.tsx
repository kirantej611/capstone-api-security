'use client';

import React, { useState } from 'react';
import {
  Zap,
  Shield,
  ShieldAlert,
  Flame,
  Play,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  Terminal,
  AlertTriangle,
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
      console.error('Failed to trigger attack scenario:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const runAutomatedPresentation = async () => {
    setNarrativeRunning(true);

    const sequence = [
      { id: 'normal-customer-flow', text: '1/4: Simulating clean legitimate customer traffic...' },
      { id: 'sqli-auth-bypass', text: "2/4: Simulating SQL Injection auth bypass on login..." },
      { id: 'xss-product-review', text: '3/4: Simulating Stored XSS cookie stealer injection...' },
      { id: 'credential-stuffing-burst', text: '4/4: Simulating rapid credential stuffing burst...' },
    ];

    for (const step of sequence) {
      setNarrativeStep(step.text);
      const sc = ATTACK_SCENARIOS.find((s) => s.id === step.id);
      if (sc) {
        setSelectedScenario(sc);
        await runAttack(sc, true);
        await new Promise((r) => setTimeout(r, 2200));
      }
    }

    setNarrativeStep('Automated Demo Complete. All threats successfully neutralized!');
    setTimeout(() => {
      setNarrativeRunning(false);
      setNarrativeStep('');
    }, 3000);
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      {/* Panel Top Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1rem',
        }}
      >
        <div className="panel-title-wrap">
          <Zap size={22} color="#f59e0b" />
          <div>
            <h2 className="panel-title" style={{ fontSize: '1.15rem' }}>
              Interactive Attack Simulation Studio & Business Demo Suite
            </h2>
            <span className="panel-subtitle">
              Validate deep-learning defense efficacy in real-time • Compare Protected vs Unprotected impact
            </span>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={runAutomatedPresentation}
          disabled={isRunning || narrativeRunning}
          style={{
            background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
            boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)',
          }}
        >
          <Sparkles size={15} />
          <span>{narrativeRunning ? narrativeStep : 'Run 30-Second Executive Demo Narrative'}</span>
        </button>
      </div>

      {/* Scenario Selection Grid */}
      <div className="scenario-grid">
        {ATTACK_SCENARIOS.map((sc) => {
          const isSelected = selectedScenario.id === sc.id;
          return (
            <div
              key={sc.id}
              className="scenario-card"
              style={{
                borderColor: isSelected ? 'var(--accent-blue)' : 'var(--border-subtle)',
                background: isSelected ? 'rgba(59, 130, 246, 0.08)' : 'rgba(15, 23, 42, 0.6)',
              }}
              onClick={() => setSelectedScenario(sc)}
            >
              <div>
                <div className="scenario-header">
                  <h4 style={{ color: '#fff', fontSize: '0.88rem', fontWeight: 600 }}>
                    {sc.title}
                  </h4>
                  <span className={`risk-pill risk-${sc.severity}`}>{sc.severity}</span>
                </div>

                <div
                  className="font-mono"
                  style={{
                    fontSize: '0.72rem',
                    color: '#93c5fd',
                    marginBottom: '0.5rem',
                    background: 'rgba(0,0,0,0.3)',
                    padding: '3px 6px',
                    borderRadius: '4px',
                    display: 'inline-block',
                  }}
                >
                  {sc.method} {sc.targetEndpoint}
                </div>

                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  {sc.description}
                </p>
              </div>

              <div className="scenario-btn-group">
                <button
                  className="btn-primary"
                  style={{ flex: 1, padding: '0.45rem 0.6rem' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedScenario(sc);
                    runAttack(sc, true);
                  }}
                  disabled={isRunning}
                >
                  <Shield size={13} />
                  <span>With AI Shield (:8080)</span>
                </button>

                <button
                  className="btn-danger"
                  style={{ padding: '0.45rem 0.6rem' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedScenario(sc);
                    runAttack(sc, false);
                  }}
                  disabled={isRunning}
                  title="Fire directly at vulnerable victim backend"
                >
                  <Flame size={13} />
                  <span>Direct (:8081)</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live A/B Execution Console */}
      {lastResult && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1.25rem',
            borderRadius: 'var(--radius-lg)',
            background: '#070c18',
            border: `1px solid ${
              lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                ? 'rgba(16, 185, 129, 0.4)'
                : lastResult.mode === 'UNPROTECTED' && lastResult.statusCode === 200 && lastResult.scenario.category !== 'Normal'
                ? 'rgba(239, 68, 68, 0.4)'
                : 'rgba(59, 130, 246, 0.3)'
            }`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <Terminal size={18} color="#60a5fa" />
              <div>
                <h3 style={{ fontSize: '0.95rem', color: '#fff' }}>
                  Execution Response Telemetry — {lastResult.scenario.title}
                </h3>
                <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                  Target: {lastResult.mode === 'SHIELD' ? 'API Gateway Shield (:8080)' : 'Unprotected Victim Backend (:8081)'} • {lastResult.timestamp}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="font-mono" style={{ fontSize: '0.8rem', color: '#93c5fd' }}>
                <Clock size={13} style={{ display: 'inline', marginRight: '4px' }} />
                {lastResult.latencyMs}ms roundtrip
              </div>

              <span
                className={`badge ${
                  lastResult.statusCode === 403
                    ? 'badge-block'
                    : lastResult.statusCode === 200
                    ? 'badge-allow'
                    : 'badge-rate-limit'
                }`}
                style={{ fontSize: '0.8rem', padding: '4px 10px' }}
              >
                HTTP {lastResult.statusCode}
              </span>
            </div>
          </div>

          {/* Business Comparison Callout Box */}
          <div
            style={{
              padding: '0.85rem 1rem',
              borderRadius: 'var(--radius-md)',
              marginBottom: '1rem',
              background:
                lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                  ? 'rgba(16, 185, 129, 0.1)'
                  : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(59, 130, 246, 0.1)',
              border: `1px solid ${
                lastResult.mode === 'SHIELD' && lastResult.statusCode === 403
                  ? 'rgba(16, 185, 129, 0.3)'
                  : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal'
                  ? 'rgba(239, 68, 68, 0.3)'
                  : 'rgba(59, 130, 246, 0.3)'
              }`,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              {lastResult.mode === 'SHIELD' && lastResult.statusCode === 403 ? (
                <>
                  <CheckCircle size={15} color="#10b981" />
                  <span style={{ color: '#6ee7b7' }}>AI Shield Successfully Defended Asset!</span>
                </>
              ) : lastResult.mode === 'UNPROTECTED' && lastResult.scenario.category !== 'Normal' ? (
                <>
                  <AlertTriangle size={15} color="#ef4444" />
                  <span style={{ color: '#fca5a5' }}>VULNERABILITY EXPLOITED! (Direct Target Breached)</span>
                </>
              ) : (
                <>
                  <CheckCircle size={15} color="#3b82f6" />
                  <span style={{ color: '#93c5fd' }}>Legitimate Traffic Cleanly Delivered</span>
                </>
              )}
            </div>

            <p style={{ fontSize: '0.75rem', color: '#e2e8f0', lineHeight: 1.45 }}>
              {lastResult.mode === 'SHIELD'
                ? lastResult.scenario.explanation
                : 'Without the AI Shield gateway in front, the victim application blindly executed the malicious input against the PostgreSQL database or system shell, resulting in unauthorized data exposure.'}
            </p>
          </div>

          {/* Response Raw Body */}
          <div className="code-block" style={{ maxHeight: '180px' }}>
            {typeof lastResult.body === 'object'
              ? JSON.stringify(lastResult.body, null, 2)
              : lastResult.body}
          </div>
        </div>
      )}
    </div>
  );
}
