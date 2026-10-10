'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  DEMO_SCENARIOS,
  DemoAttempt,
  compareDemoScenario,
  executeDemoRequest,
} from '../../lib/demoClient';
import { AttackScenario } from '../../lib/types';

function AttemptCard({ attempt }: { attempt: DemoAttempt | null }) {
  if (!attempt) {
    return <div className="shop-empty">No result yet.</div>;
  }
  return (
    <article className="review-item">
      <h3>{attempt.label}</h3>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{attempt.targetUrl}</p>
      {attempt.error ? (
        <div className="shop-alert error">{attempt.error}</div>
      ) : (
        <p>
          HTTP {attempt.statusCode} · {attempt.latencyMs}ms
        </p>
      )}
      <pre
        style={{
          background: '#111827',
          color: '#f9fafb',
          padding: '0.85rem',
          borderRadius: '8px',
          overflowX: 'auto',
          fontSize: '0.78rem',
        }}
      >
        {attempt.error
          ? 'No response body — the service did not answer.'
          : typeof attempt.body === 'string'
            ? attempt.body
            : JSON.stringify(attempt.body, null, 2)}
      </pre>
    </article>
  );
}

export default function DemoPage() {
  const [scenario, setScenario] = useState<AttackScenario>(DEMO_SCENARIOS[0]);
  const [protectedAttempt, setProtectedAttempt] = useState<DemoAttempt | null>(null);
  const [unprotectedAttempt, setUnprotectedAttempt] = useState<DemoAttempt | null>(null);
  const [pending, setPending] = useState(false);

  const run = async (mode: 'protected' | 'unprotected' | 'both') => {
    setPending(true);
    try {
      if (mode === 'both') {
        const result = await compareDemoScenario(scenario);
        setProtectedAttempt(result.protected);
        setUnprotectedAttempt(result.unprotected);
      } else if (mode === 'protected') {
        setProtectedAttempt(await executeDemoRequest(scenario, 'protected'));
      } else {
        setUnprotectedAttempt(await executeDemoRequest(scenario, 'unprotected'));
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="shop-body" style={{ minHeight: '100vh', padding: '1.5rem' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <p style={{ marginBottom: '0.75rem' }}>
          <Link href="/">Security dashboard</Link> · <Link href="/shop">Customer store</Link>
        </p>
        <h1>Shield vs direct demo</h1>
        <p style={{ color: '#52606d', maxWidth: 720, margin: '0.5rem 0 1rem' }}>
          This page sends one preconfigured local scenario through the API gateway and, separately,
          directly to the loopback victim service. Results are the real HTTP status and body.
          If a service is offline, you will see a connection error — never a fabricated success or block.
        </p>
        <div className="shop-alert error" style={{ background: '#fff7ed', borderColor: '#fdba74', color: '#9a3412' }}>
          Direct victim access is an opt-in local demo path only (127.0.0.1:8081). Do not expose it on public interfaces.
        </div>

        <label style={{ display: 'block', margin: '1rem 0 0.5rem' }}>Scenario</label>
        <select
          className="shop-select"
          value={scenario.id}
          onChange={(e) => {
            const next = DEMO_SCENARIOS.find((item) => item.id === e.target.value);
            if (next) setScenario(next);
          }}
        >
          {DEMO_SCENARIOS.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title}
            </option>
          ))}
        </select>
        <p style={{ margin: '0.75rem 0', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
          {scenario.method} {scenario.targetEndpoint}
        </p>
        <p style={{ color: '#52606d', marginBottom: '1rem' }}>{scenario.description}</p>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <button className="shop-btn" type="button" disabled={pending} onClick={() => run('protected')}>
            Protected (through shield)
          </button>
          <button className="shop-btn-secondary" type="button" disabled={pending} onClick={() => run('unprotected')}>
            Unprotected (direct to victim)
          </button>
          <button className="shop-btn" type="button" disabled={pending} onClick={() => run('both')}>
            Compare both
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <AttemptCard attempt={protectedAttempt} />
          <AttemptCard attempt={unprotectedAttempt} />
        </div>
      </div>
    </div>
  );
}
