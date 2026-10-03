package models

import "time"

// GatewayVerdict matches the GatewayVerdict Pydantic model published by the
// api-gateway to the "api.verdicts" Kafka topic.
type GatewayVerdict struct {
	RequestID         string   `json:"request_id"`
	Timestamp         string   `json:"timestamp"`
	ClientIP          string   `json:"client_ip"`
	Method            string   `json:"method"`
	Path              string   `json:"path"`
	Action            string   `json:"action"`            // "allow" | "block" | "flag" | "rate_limit"
	BlockReason       string   `json:"block_reason"`      // optional
	AnomalyScore      float64  `json:"anomaly_score"`     // optional, 0 if absent
	IsAnomalous       bool     `json:"is_anomalous"`      // optional
	ThreatType        string   `json:"threat_type"`       // optional attack category
	ThreatConfidence  float64  `json:"threat_confidence"` // optional 0-1
	RiskLevel         string   `json:"risk_level"`        // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
	MLLatencyMs       float64  `json:"ml_latency_ms"`
	TotalLatencyMs    float64  `json:"total_latency_ms"`
}

// IsAttack returns true if the gateway flagged or blocked this request via ML
func (v *GatewayVerdict) IsAttack() bool {
	return v.IsAnomalous || v.ThreatType != "" || v.Action == "block"
}

// Alert to store in Postgres
type Alert struct {
	ID         int       `json:"id"`
	SourceIP   string    `json:"source_ip"`
	AttackType string    `json:"attack_type"`
	Severity   string    `json:"severity"`
	Details    string    `json:"details"`
	Timestamp  time.Time `json:"timestamp"`
}

// IPRisk summarises a source IP's risk posture
type IPRisk struct {
	IP          string  `json:"ip"`
	Score       float64 `json:"score"`
	IsBlocked   bool    `json:"is_blocked"`
	LastUpdated string  `json:"last_updated"`
}
