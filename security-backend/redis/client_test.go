package redis

import "testing"

func TestBlocklistKeyMatchesGatewayPrefix(t *testing.T) {
	const ip = "198.51.100.42"
	want := "blocklist:ip:" + ip
	if got := BlocklistKey(ip); got != want {
		t.Errorf("BlocklistKey() = %q, want %q", got, want)
	}
}

func TestRiskScoreKey(t *testing.T) {
	const ip = "198.51.100.42"
	want := "risk_score:" + ip
	if got := RiskScoreKey(ip); got != want {
		t.Errorf("RiskScoreKey() = %q, want %q", got, want)
	}
}
