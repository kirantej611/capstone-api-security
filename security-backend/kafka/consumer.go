package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/kirantej611/capstone-api-security/security-backend/api"
	"github.com/kirantej611/capstone-api-security/security-backend/config"
	"github.com/kirantej611/capstone-api-security/security-backend/db"
	"github.com/kirantej611/capstone-api-security/security-backend/models"
	rdb "github.com/kirantej611/capstone-api-security/security-backend/redis"
	kafka "github.com/segmentio/kafka-go"
)

// StartConsumer reads GatewayVerdict messages from the "api.verdicts" topic
// published by the api-gateway service, scores each source IP, and blocks
// IPs whose cumulative risk score exceeds the configured threshold.
func StartConsumer(cfg config.Config) {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  []string{cfg.KafkaBrokers},
		Topic:    cfg.KafkaTopic, // "api.verdicts"
		GroupID:  "security-backend-group",
		MinBytes: 1,
		MaxBytes: 10e6,
	})

	log.Printf("[kafka] Listening on topic=%s broker=%s", cfg.KafkaTopic, cfg.KafkaBrokers)

	go func() {
		defer r.Close()
		for {
			m, err := r.ReadMessage(context.Background())
			if err != nil {
				log.Printf("[kafka] Read error: %v", err)
				continue
			}
			processVerdict(m.Value, cfg)
		}
	}()
}

func processVerdict(raw []byte, cfg config.Config) {
	var v models.GatewayVerdict
	if err := json.Unmarshal(raw, &v); err != nil {
		log.Printf("[kafka] Failed to parse verdict: %v", err)
		return
	}

	// Only process requests that the ML engine flagged as attacks
	if !v.IsAttack() {
		return
	}

	log.Printf("[risk] Attack from %s | type=%s | confidence=%.2f | action=%s",
		v.ClientIP, v.ThreatType, v.ThreatConfidence, v.Action)

	// Broadcast real-time verdict telemetry to connected dashboard WebSocket clients
	api.AlertHub.Broadcast(v)

	// --- Risk Score Calculation ---
	// Base increment: 10 pts for any attack signal
	// Multiplied by threat confidence (0–1) if available → up to 100 pts per hit
	increment := 10.0
	if v.ThreatConfidence > 0 {
		increment = v.ThreatConfidence * 100
	} else if v.AnomalyScore > 0 {
		increment = v.AnomalyScore * 20
	}

	// Bump score for already-blocked IPs (they shouldn't be reaching us, but handle it)
	if v.Action == "block" {
		increment *= 1.5
	}

	newScore, err := rdb.IncrementRiskScore(v.ClientIP, increment)
	if err != nil {
		log.Printf("[risk] Redis error for %s: %v", v.ClientIP, err)
		return
	}
	log.Printf("[risk] IP %s score=%.2f threshold=%.2f", v.ClientIP, newScore, cfg.BlockThreshold)

	// --- Threshold Enforcement ---
	if newScore >= cfg.BlockThreshold {
		if err := rdb.BlockIP(v.ClientIP); err != nil {
			log.Printf("[risk] Failed to block %s: %v", v.ClientIP, err)
		}

		severity := severityFromRisk(v.RiskLevel)
		alert := models.Alert{
			SourceIP:   v.ClientIP,
			AttackType: v.ThreatType,
			Severity:   severity,
			Details: fmt.Sprintf(
				"IP blocked after risk score %.2f exceeded threshold %.2f. "+
					"Last attack: %s on %s %s (confidence %.2f)",
				newScore, cfg.BlockThreshold,
				v.ThreatType, v.Method, v.Path, v.ThreatConfidence,
			),
		}
		if err := db.SaveAlert(alert); err != nil {
			log.Printf("[db] Failed to save alert: %v", err)
		} else {
			log.Printf("[db] Alert saved for %s (%s)", v.ClientIP, v.ThreatType)
			api.AlertHub.Broadcast(alert)
			if alertBytes, err := json.Marshal(alert); err == nil {
				api.SSESubscribers.Broadcast(string(alertBytes))
			}
		}
	}
}

// severityFromRisk maps gateway RiskLevel string to our severity labels
func severityFromRisk(riskLevel string) string {
	switch riskLevel {
	case "CRITICAL":
		return "CRITICAL"
	case "HIGH":
		return "HIGH"
	case "MEDIUM":
		return "MEDIUM"
	default:
		return "LOW"
	}
}
