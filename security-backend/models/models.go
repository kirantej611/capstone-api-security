package models

import "time"

// Prediction from ML Engine
type MLPrediction struct {
	Timestamp      string  `json:"timestamp"`
	SourceIP       string  `json:"source_ip"`
	Endpoint       string  `json:"endpoint"`
	Method         string  `json:"method"`
	IsAttack       bool    `json:"is_attack"`
	AttackType     string  `json:"attack_type,omitempty"`
	AnomalyScore   float64 `json:"anomaly_score,omitempty"`
	ClassifierConf float64 `json:"classifier_confidence,omitempty"`
}

// Alert to store in DB
type Alert struct {
	ID         int       `json:"id"`
	SourceIP   string    `json:"source_ip"`
	AttackType string    `json:"attack_type"`
	Severity   string    `json:"severity"`
	Details    string    `json:"details"`
	Timestamp  time.Time `json:"timestamp"`
}

// IP Risk Profile
type IPRisk struct {
	IP          string  `json:"ip"`
	Score       float64 `json:"score"`
	IsBlocked   bool    `json:"is_blocked"`
	LastUpdated string  `json:"last_updated"`
}
