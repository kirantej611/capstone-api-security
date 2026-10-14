import { ATTACK_SCENARIOS } from './xaiUtils';
import { AttackScenario } from './types';
import { getGatewayUrl, getVictimUrl } from './serviceUrls';

export const DEMO_SCENARIOS: AttackScenario[] = ATTACK_SCENARIOS;

const ALLOWED_ENDPOINTS = new Set(
  DEMO_SCENARIOS.map((scenario) => scenario.targetEndpoint.split('?')[0])
);

export type DemoRoute = 'protected' | 'unprotected';

export interface DemoAttempt {
  route: DemoRoute;
  label: string;
  targetUrl: string;
  ok: boolean;
  statusCode: number | null;
  body: unknown;
  latencyMs: number;
  error: string | null;
}

function isLoopbackHost(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1';
  } catch {
    return false;
  }
}

function assertAllowedEndpoint(endpoint: string) {
  const path = endpoint.split('?')[0];
  if (!ALLOWED_ENDPOINTS.has(path) && !ALLOWED_ENDPOINTS.has(endpoint)) {
    const allowed = DEMO_SCENARIOS.some((scenario) => scenario.targetEndpoint === endpoint);
    if (!allowed) {
      throw new Error('This demo only allows preconfigured local endpoints.');
    }
  }
}

export async function executeDemoRequest(
  scenario: AttackScenario,
  route: DemoRoute
): Promise<DemoAttempt> {
  assertAllowedEndpoint(scenario.targetEndpoint);

  const base = route === 'protected' ? getGatewayUrl() : getVictimUrl();
  const label =
    route === 'protected'
      ? 'Protected (through shield)'
      : 'Unprotected (direct to victim)';

  if (route === 'unprotected' && !isLoopbackHost(base)) {
    return {
      route,
      label,
      targetUrl: `${base}${scenario.targetEndpoint}`,
      ok: false,
      statusCode: null,
      body: null,
      latencyMs: 0,
      error:
        'Direct victim access is limited to the local demo (localhost / 127.0.0.1). The request was not sent.',
    };
  }

  const targetUrl = `${base}${scenario.targetEndpoint}`;
  const started = performance.now();

  try {
    const response = await fetch(targetUrl, {
      method: scenario.method,
      headers: {
        Accept: 'application/json',
        ...(scenario.method === 'POST' ? { 'Content-Type': 'application/json' } : {}),
        'X-Demo-Source': 'local-shield-vs-direct-demo',
      },
      body:
        scenario.method === 'POST'
          ? JSON.stringify(scenario.payload || {})
          : undefined,
      cache: 'no-store',
      signal: AbortSignal.timeout(8000),
    });

    const latencyMs = Math.round(performance.now() - started);
    const contentType = response.headers.get('content-type') || '';
    let body: unknown;
    if (contentType.includes('application/json')) {
      body = await response.json();
    } else {
      body = await response.text();
    }

    return {
      route,
      label,
      targetUrl,
      ok: true,
      statusCode: response.status,
      body,
      latencyMs,
      error: null,
    };
  } catch (err) {
    const latencyMs = Math.round(performance.now() - started);
    const service = route === 'protected' ? 'API gateway (:8080)' : 'victim backend (:8081)';
    return {
      route,
      label,
      targetUrl,
      ok: false,
      statusCode: null,
      body: null,
      latencyMs,
      error: `Cannot reach ${service}. ${err instanceof Error ? err.message : 'Network error'}. This is a connection failure, not a blocked or successful attack.`,
    };
  }
}

export async function compareDemoScenario(scenario: AttackScenario): Promise<{
  protected: DemoAttempt;
  unprotected: DemoAttempt;
}> {
  const [protectedAttempt, unprotectedAttempt] = await Promise.all([
    executeDemoRequest(scenario, 'protected'),
    executeDemoRequest(scenario, 'unprotected'),
  ]);
  return { protected: protectedAttempt, unprotected: unprotectedAttempt };
}
