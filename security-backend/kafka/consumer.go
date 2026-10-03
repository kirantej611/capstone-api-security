package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/kirantej611/capstone-api-security/security-backend/config"
	"github.com/kirantej611/capstone-api-security/security-backend/db"
	"github.com/kirantej611/capstone-api-security/security-backend/models"
	rdb "github.com/kirantej611/capstone-api-security/security-backend/redis"
	"github.com/segmentio/kafka-go"
)

func StartConsumer(cfg config.Config) {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers: []string{cfg.KafkaBrokers},
		Topic:   cfg.KafkaTopic,
		GroupID: "security-backend-group",
	})

	log.Printf("Listening for Kafka messages on topic: %s", cfg.KafkaTopic)

	go func() {
		for {
			m, err := r.ReadMessage(context.Background())
			if err != nil {
				log.Printf("Error reading kafka message: %v", err)
				continue
			}
			processMessage(m.Value, cfg)
		}
	}()
}

func processMessage(value []byte, cfg config.Config) {
	var pred models.MLPrediction
	if err := json.Unmarshal(value, &pred); err != nil {
		log.Printf("Error parsing prediction: %v", err)
		return
	}

	// Only process attacks
	if !pred.IsAttack {
		return
	}

	log.Printf("Attack detected from %s: %s (Confidence: %.2f)", pred.SourceIP, pred.AttackType, pred.ClassifierConf)

	// Calculate score increment based on confidence
	increment := 10.0
	if pred.ClassifierConf > 0 {
		increment = pred.ClassifierConf * 100 // up to 100 points
	} else if pred.AnomalyScore > 0 {
		increment = pred.AnomalyScore * 5 // anomaly scores vary
	}

	// Update Risk Score in Redis
	newScore, err := rdb.IncrementRiskScore(pred.SourceIP, increment)
	if err != nil {
		log.Printf("Failed to update risk score: %v", err)
		return
	}

	log.Printf("IP %s new risk score: %.2f", pred.SourceIP, newScore)

	// Check threshold for blocking
	if newScore >= cfg.BlockThreshold {
		rdb.BlockIP(pred.SourceIP)
		
		// Save Alert to Postgres
		alert := models.Alert{
			SourceIP:   pred.SourceIP,
			AttackType: pred.AttackType,
			Severity:   "HIGH",
			Details:    fmt.Sprintf("Risk score (%.2f) exceeded threshold (%.2f)", newScore, cfg.BlockThreshold),
		}
		if err := db.SaveAlert(alert); err != nil {
			log.Printf("Failed to save alert: %v", err)
		}
	}
}
