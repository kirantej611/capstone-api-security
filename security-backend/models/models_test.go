package models

import (
	"encoding/json"
	"testing"
)

func TestGatewayVerdictIsAttack(t *testing.T) {
	tests := []struct {
		name string
		json string
		want bool
	}{
		{
			name: "normal prediction is not an attack",
			json: `{"action":"ALLOW","threat_type":"Normal","is_anomalous":false}`,
			want: false,
		},
		{
			name: "IP blocklist decision is not an ML attack",
			json: `{"action":"BLOCK","block_reason":"IP_BLOCKLISTED"}`,
			want: false,
		},
		{
			name: "rate limit decision is not an ML attack",
			json: `{"action":"RATE_LIMIT","block_reason":"RATE_LIMIT_EXCEEDED"}`,
			want: false,
		},
		{
			name: "flagged anomaly is an attack",
			json: `{"action":"FLAG","threat_type":"XSS","is_anomalous":true}`,
			want: true,
		},
		{
			name: "ML block reason remains an attack without anomaly field",
			json: `{"action":"BLOCK","block_reason":"ML_THREAT_DETECTED"}`,
			want: true,
		},
		{
			name: "action and reason matching is case insensitive",
			json: `{"action":"block","block_reason":"ml_threat_detected"}`,
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var verdict GatewayVerdict
			if err := json.Unmarshal([]byte(tt.json), &verdict); err != nil {
				t.Fatalf("unmarshal verdict: %v", err)
			}
			if got := verdict.IsAttack(); got != tt.want {
				t.Errorf("IsAttack() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGatewayVerdictIsBlocked(t *testing.T) {
	for action, want := range map[string]bool{
		"BLOCK":      true,
		"block":      true,
		"ALLOW":      false,
		"RATE_LIMIT": false,
	} {
		verdict := GatewayVerdict{Action: action}
		if got := verdict.IsBlocked(); got != want {
			t.Errorf("IsBlocked() for action %q = %v, want %v", action, got, want)
		}
	}
}
