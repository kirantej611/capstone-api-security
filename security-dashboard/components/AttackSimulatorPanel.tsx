'use client';

import React, { useState } from 'react';
import { Shield, Flame, Clock, Terminal } from 'lucide-react';
import Link from 'next/link';
import { DEMO_SCENARIOS, DemoAttempt, executeDemoRequest } from '../lib/demoClient';
import { AttackScenario } from '../lib/types';

export default function AttackSimulatorPanel() {
  const [selectedScenario, setSelectedScenario] = useState<AttackScenario>(DEMO_SCENARIOS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [lastResult, setLastResult] = useState<DemoAttempt | null>(null);

  const runAttack = async (scenario: AttackScenario, route: 'protected' | 'unprotected') => {
    setIsRunning(true);
    setSelectedScenario(scenario);
    try {
      setLastResult(await executeDemoRequest(scenario, route));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="white-card">
      <div className="card-header-row" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 className="card-title">Attack simulation studio</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Sends a preconfigured local scenario through the shield or directly to the loopback victim service.
            Offline services show a connection error. Side-by-side comparison lives on the dedicated demo page.
          </span>
        </div>
        <Link href="/demo" className="hub-btn-primary" style={{ textDecoration: 'none' }}>
          Open shield vs direct demo
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
        {DEMO_SCENARIOS.map((sc) => {
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
              }}
            >
              <h4 style={{ fontSize: '0.88rem', fontWeight: 600 }}>{sc.title}</h4>
              <div className="font-mono" style={{ fontSize: '0.72rem', color: '#0284c7', margin: '0.4rem 0' }}>
                {sc.method} {sc.targetEndpoint}
              </div>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{sc.description}</p>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button
                  className="hub-btn-primary"
                  style={{ flex: 1, padding: '0.4rem 0.6rem', fontSize: '0.75rem', justifyContent: 'center' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    runAttack(sc, 'protected');
                  }}
                  disabled={isRunning}
                >
                  <Shield size={13} />
                  <span>Protected (through shield)</span>
                </button>
                <button
                  className="hub-btn-danger"
                  style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', justifyContent: 'center' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    runAttack(sc, 'unprotected');
                  }}
                  disabled={isRunning}
                >
                  <Flame size={13} />
                  <span>Unprotected (direct)</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {lastResult && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1.25rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-light)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Terminal size={17} color="#0284c7" />
              <strong>{lastResult.label}</strong>
            </div>
            <span className="font-mono" style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              <Clock size={12} style={{ display: 'inline', marginRight: '3px' }} />
              {lastResult.latencyMs}ms
              {lastResult.statusCode !== null ? ` · HTTP ${lastResult.statusCode}` : ''}
            </span>
          </div>
          <p className="font-mono" style={{ fontSize: '0.74rem', margin: '0.65rem 0' }}>
            {lastResult.targetUrl}
          </p>
          {lastResult.error ? (
            <div className="shop-alert error" style={{ background: '#fef2f2', color: '#991b1b', padding: '0.75rem', borderRadius: 8 }}>
              {lastResult.error}
            </div>
          ) : (
            <pre
              style={{
                background: '#0f172a',
                color: '#f8fafc',
                padding: '0.85rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.74rem',
                overflowX: 'auto',
              }}
            >
              {typeof lastResult.body === 'string' ? lastResult.body : JSON.stringify(lastResult.body, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
