import {
  BlockedIPEntry,
  GatewayStats,
  HealthResponse,
  Product,
  ProductReview,
  RecentVerdict,
} from './types';
import {
  INITIAL_PRODUCTS,
  INITIAL_REVIEWS,
} from './mockData';

export const EMPTY_STATS: GatewayStats = {
  total_requests: 0,
  allowed_requests: 0,
  blocked_requests: 0,
  rate_limited_requests: 0,
  flagged_requests: 0,
  avg_ml_latency_ms: 0,
  active_blocked_ips: 0,
  uptime_seconds: 0,
  requests_per_second: 0,
};

// State container for in-memory fallback/simulation mode
class DashboardStore {
  stats: GatewayStats = { ...EMPTY_STATS };
  verdicts: RecentVerdict[] = [];
  blockedIps: BlockedIPEntry[] = [];
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
      const mapped: BlockedIPEntry[] = (json.blocked_ips || []).map((ip: string) => ({ ip }));
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
    throw new Error(`Gateway returned HTTP ${res.status}`);
  } catch (e) {
    throw e instanceof Error ? e : new Error('Cannot reach the API gateway');
  }
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
    throw new Error(`Gateway returned HTTP ${res.status}`);
  } catch (e) {
    throw e instanceof Error ? e : new Error('Cannot reach the API gateway');
  }
}

/**
 * Gateway Health Check
 */
export async function fetchHealth(): Promise<{ data: HealthResponse | null; isLive: boolean }> {
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
  return { data: null, isLive: false };
}

export { executeDemoRequest as executeSimulatedRequest } from './demoClient';
