export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type GatewayAction = 'ALLOW' | 'BLOCK' | 'RATE_LIMIT' | 'FLAG';
export type BlockReason =
  | 'ML_THREAT_DETECTED'
  | 'IP_BLOCKLISTED'
  | 'RATE_LIMIT_EXCEEDED'
  | 'ML_ENGINE_UNAVAILABLE'
  | 'MANUAL_ADMIN_BLOCK';

export type ThreatType =
  | 'Normal'
  | 'SQLi'
  | 'XSS'
  | 'Path Traversal'
  | 'Command Injection'
  | 'Credential Stuffing'
  | 'BOLA / Broken Object Auth';

export interface MLPredictResponse {
  anomaly_score: number;
  is_anomalous: boolean;
  threat_type: ThreatType;
  threat_confidence: number;
  all_probabilities: Record<string, number>;
  risk_level: RiskLevel;
  feature_importance: Record<string, number>;
}

export interface RecentVerdict {
  request_id: string;
  timestamp: string;
  client_ip: string;
  method: string;
  path: string;
  action: GatewayAction;
  threat_type?: ThreatType | string | null;
  risk_level?: RiskLevel | string | null;
  anomaly_score?: number | null;
  // Extended fields for rich drilldown
  headers?: Record<string, string>;
  body?: string;
  query_params?: Record<string, string>;
  block_reason?: BlockReason | string | null;
  threat_confidence?: number | null;
  all_probabilities?: Record<string, number> | null;
  feature_importance?: Record<string, number> | null;
  ml_latency_ms?: number | null;
  total_latency_ms?: number | null;
  attack_payload_highlight?: string | null;
}

export interface GatewayStats {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  rate_limited_requests: number;
  flagged_requests: number;
  avg_ml_latency_ms: number;
  active_blocked_ips: number;
  uptime_seconds: number;
  requests_per_second: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  service: string;
  redis_connected: boolean;
  kafka_connected: boolean;
  ml_engine_connected: boolean;
  victim_ecommerce_connected?: boolean;
  uptime_seconds: number;
}

export interface BlockedIPEntry {
  ip: string;
  reason: string;
  blocked_at: string;
  ttl_remaining_seconds: number;
  severity: RiskLevel;
}

export interface AttackScenario {
  id: string;
  title: string;
  category: ThreatType;
  severity: RiskLevel;
  targetEndpoint: string;
  method: 'GET' | 'POST';
  description: string;
  payload: string | Record<string, any>;
  explanation: string;
  cwe: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  stock: number;
  rating?: number;
  image?: string;
}

export interface ProductReview {
  id: number;
  product_id: number;
  user_id: number;
  username?: string;
  rating: number;
  comment: string;
  created_at?: string;
}
