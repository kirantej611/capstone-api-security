import {
  BlockedIPEntry,
  GatewayStats,
  HealthResponse,
  Product,
  ProductReview,
  RecentVerdict,
} from './types';
import {
  INITIAL_BLOCKED_IPS,
  INITIAL_PRODUCTS,
  INITIAL_REVIEWS,
  INITIAL_STATS,
  INITIAL_VERDICTS,
} from './mockData';

// State container for in-memory fallback/simulation mode
class DashboardStore {
  stats: GatewayStats = { ...INITIAL_STATS };
  verdicts: RecentVerdict[] = [...INITIAL_VERDICTS];
  blockedIps: BlockedIPEntry[] = [...INITIAL_BLOCKED_IPS];
  products: Product[] = [...INITIAL_PRODUCTS];
  reviews: ProductReview[] = [...INITIAL_REVIEWS];
  isLiveGateway = false;
  isVictimBackendLive = false;
  isSimulatorActive = true;
  lastError: string | null = null;

  recordSimulatedVerdict(verdict: RecentVerdict) {
    this.verdicts.unshift(verdict);
    if (this.verdicts.length > 100) this.verdicts.pop();

    this.stats.total_requests += 1;
    if (verdict.action === 'BLOCK') {
      this.stats.blocked_requests += 1;
    } else if (verdict.action === 'ALLOW') {
      this.stats.allowed_requests += 1;
    } else if (verdict.action === 'RATE_LIMIT') {
      this.stats.rate_limited_requests += 1;
    } else if (verdict.action === 'FLAG') {
      this.stats.flagged_requests += 1;
    }

    if (verdict.risk_level === 'CRITICAL' && verdict.client_ip) {
      if (!this.blockedIps.some((b) => b.ip === verdict.client_ip)) {
        this.blockedIps.unshift({
          ip: verdict.client_ip,
          reason: `ML_CRITICAL:${verdict.threat_type}`,
          blocked_at: new Date().toISOString(),
          ttl_remaining_seconds: 3600,
          severity: 'CRITICAL',
        });
        this.stats.active_blocked_ips = this.blockedIps.length;
      }
    }
  }

  addBlockedIp(ip: string, reason = 'manual_block') {
    if (!this.blockedIps.some((b) => b.ip === ip)) {
      this.blockedIps.unshift({
        ip,
        reason,
        blocked_at: new Date().toISOString(),
        ttl_remaining_seconds: 3600,
        severity: 'HIGH',
      });
      this.stats.active_blocked_ips = this.blockedIps.length;
    }
  }

  removeBlockedIp(ip: string) {
    this.blockedIps = this.blockedIps.filter((b) => b.ip !== ip);
    this.stats.active_blocked_ips = this.blockedIps.length;
  }
}

export const localStore = new DashboardStore();

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8080';
const VICTIM_URL = process.env.NEXT_PUBLIC_VICTIM_URL || 'http://localhost:8081';

/**
 * Fetch Gateway Statistics
 */
export async function fetchGatewayStats(): Promise<{ data: GatewayStats; isLive: boolean }> {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/stats`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const data: GatewayStats = await res.json();
      localStore.isLiveGateway = true;
      return { data, isLive: true };
    }
  } catch (err) {
    // Gateway not running yet
  }
  localStore.isLiveGateway = false;
  return { data: { ...localStore.stats }, isLive: false };
}

/**
 * Fetch Recent Verdicts
 */
export async function fetchRecentVerdicts(
  limit = 50
): Promise<{ data: RecentVerdict[]; isLive: boolean }> {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/verdicts/recent?limit=${limit}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const data: RecentVerdict[] = await res.json();
      localStore.isLiveGateway = true;
      return { data, isLive: true };
    }
  } catch (err) {
    // Fall back to local store
  }
  localStore.isLiveGateway = false;
  return { data: [...localStore.verdicts], isLive: false };
}

/**
 * Fetch Blocklist
 */
export async function fetchBlocklist(): Promise<{ data: BlockedIPEntry[]; isLive: boolean }> {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/blocklist`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const json = await res.json();
      const mapped: BlockedIPEntry[] = (json.blocked_ips || []).map((ip: string) => ({
        ip,
        reason: 'Redis active block',
        blocked_at: new Date().toISOString(),
        ttl_remaining_seconds: 3600,
        severity: 'CRITICAL',
      }));
      localStore.isLiveGateway = true;
      return { data: mapped, isLive: true };
    }
  } catch (err) {
    // Fall back
  }
  return { data: [...localStore.blockedIps], isLive: false };
}

/**
 * Add IP to Blocklist
 */
export async function addIpToBlocklist(ip: string, reason = 'manual_admin_action') {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/blocklist/${encodeURIComponent(ip)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    // Local fallback
  }
  localStore.addBlockedIp(ip, reason);
  return { status: 'blocked', ip, reason };
}

/**
 * Remove IP from Blocklist
 */
export async function removeIpFromBlocklist(ip: string) {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/blocklist/${encodeURIComponent(ip)}`, {
      method: 'DELETE',
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    // Local fallback
  }
  localStore.removeBlockedIp(ip);
  return { status: 'unblocked', ip };
}

/**
 * Gateway Health Check
 */
export async function fetchHealth(): Promise<{ data: HealthResponse; isLive: boolean }> {
  try {
    const res = await fetch(`${GATEWAY_URL}/gateway/health`, {
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const data = await res.json();
      return { data, isLive: true };
    }
  } catch (err) {
    // offline
  }
  return {
    data: {
      status: 'healthy',
      version: '1.0.0',
      service: 'api-gateway',
      redis_connected: false,
      kafka_connected: false,
      ml_engine_connected: false,
      uptime_seconds: 86400,
    },
    isLive: false,
  };
}

/**
 * Send request either to Gateway Shield (:8080) or direct to Victim (:8081)
 */
export async function executeSimulatedRequest(
  endpoint: string,
  method: 'GET' | 'POST',
  payload: any,
  useShield = true
): Promise<{
  statusCode: number;
  body: any;
  latencyMs: number;
  verdict?: RecentVerdict;
  routedVia: string;
}> {
  const targetBase = useShield ? GATEWAY_URL : VICTIM_URL;
  const targetUrl = `${targetBase}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
  const startTime = performance.now();

  try {
    const res = await fetch(targetUrl, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Demo-Source': 'Security-Dashboard',
      },
      body: method === 'POST' ? JSON.stringify(payload) : undefined,
      signal: AbortSignal.timeout(4000),
    });
    const latency = Math.round(performance.now() - startTime);
    let parsedBody: any;
    try {
      parsedBody = await res.json();
    } catch {
      parsedBody = await res.text();
    }

    return {
      statusCode: res.status,
      body: parsedBody,
      latencyMs: latency,
      routedVia: useShield ? 'API Gateway Shield (:8080)' : 'Direct Unprotected Victim (:8081)',
    };
  } catch (err: any) {
    // If backend is not currently running, synthesize the exact response that the Gateway would give!
    const latency = Math.round(performance.now() - startTime) + 4;
    const isAttack =
      JSON.stringify(payload || '').includes("' OR '1'='1'") ||
      endpoint.includes('etc/shadow') ||
      JSON.stringify(payload || '').includes('<script') ||
      JSON.stringify(payload || '').includes('cat /etc/passwd');

    let threat_type: any = 'Normal';
    let risk_level: any = 'LOW';
    let anomaly_score = 0.04;
    let action: any = 'ALLOW';

    if (JSON.stringify(payload || '').includes("' OR '1'='1'")) {
      threat_type = 'SQLi';
      risk_level = 'CRITICAL';
      anomaly_score = 0.94;
      action = 'BLOCK';
    } else if (JSON.stringify(payload || '').includes('<script')) {
      threat_type = 'XSS';
      risk_level = 'HIGH';
      anomaly_score = 0.83;
      action = 'BLOCK';
    } else if (endpoint.includes('etc/shadow')) {
      threat_type = 'Path Traversal';
      risk_level = 'CRITICAL';
      anomaly_score = 0.92;
      action = 'BLOCK';
    } else if (JSON.stringify(payload || '').includes('cat /etc/passwd')) {
      threat_type = 'Command Injection';
      risk_level = 'CRITICAL';
      anomaly_score = 0.96;
      action = 'BLOCK';
    }

    const syntheticVerdict: RecentVerdict = {
      request_id: `req_${Math.random().toString(36).substring(2, 11)}`,
      timestamp: new Date().toISOString(),
      client_ip: '198.51.100.99',
      method,
      path: endpoint,
      action: useShield && isAttack ? 'BLOCK' : 'ALLOW',
      threat_type: isAttack ? threat_type : 'Normal',
      risk_level: isAttack ? risk_level : 'LOW',
      anomaly_score,
      threat_confidence: isAttack ? 0.975 : 0.99,
      block_reason: useShield && isAttack ? 'ML_THREAT_DETECTED' : null,
      ml_latency_ms: 3.8,
      total_latency_ms: latency,
      body: typeof payload === 'string' ? payload : JSON.stringify(payload),
      attack_payload_highlight: isAttack ? JSON.stringify(payload) : null,
    };

    localStore.recordSimulatedVerdict(syntheticVerdict);

    if (useShield && isAttack) {
      return {
        statusCode: 403,
        body: {
          error: 'threat_detected',
          detail: `Threat detected: ${threat_type} (confidence: 97.5%, risk: ${risk_level})`,
          request_id: syntheticVerdict.request_id,
          timestamp: syntheticVerdict.timestamp,
        },
        latencyMs: latency,
        verdict: syntheticVerdict,
        routedVia: 'API Gateway Shield (:8080)',
      };
    } else if (!useShield && isAttack) {
      // Unprotected victim breached!
      return {
        statusCode: 200,
        body: {
          status: 'SUCCESS',
          message: 'VULNERABILITY EXPLOITED! Backend executed unescaped query.',
          dumped_data: [
            { id: 1, username: 'admin', email: 'admin@store.com', role: 'admin' },
            { id: 2, username: 'user1', email: 'user1@store.com', role: 'customer' },
            { id: 3, username: 'user2', email: 'user2@store.com', role: 'customer' },
          ],
        },
        latencyMs: latency,
        routedVia: 'Direct Unprotected Victim (:8081)',
      };
    } else {
      return {
        statusCode: 200,
        body: { status: 'success', data: localStore.products },
        latencyMs: latency,
        verdict: syntheticVerdict,
        routedVia: useShield ? 'API Gateway Shield (:8080)' : 'Direct Unprotected Victim (:8081)',
      };
    }
  }
}
