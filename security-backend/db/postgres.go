package db

import (
	"database/sql"
	"log"

	"github.com/kirantej611/capstone-api-security/security-backend/models"
	_ "github.com/lib/pq"
)

var DB *sql.DB

func InitDB(connStr string) {
	var err error
	DB, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Failed to connect to Postgres: %v", err)
	}

	err = DB.Ping()
	if err != nil {
		log.Fatalf("Failed to ping Postgres: %v", err)
	}

	createTables()
	log.Println("Connected to Postgres successfully")
}

func createTables() {
	query := `
	CREATE TABLE IF NOT EXISTS alerts (
		id SERIAL PRIMARY KEY,
		source_ip VARCHAR(50) NOT NULL,
		attack_type VARCHAR(100),
		severity VARCHAR(20),
		details TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`
	_, err := DB.Exec(query)
	if err != nil {
		log.Fatalf("Failed to create tables: %v", err)
	}
}

func SaveAlert(alert models.Alert) error {
	query := `INSERT INTO alerts (source_ip, attack_type, severity, details) VALUES ($1, $2, $3, $4)`
	_, err := DB.Exec(query, alert.SourceIP, alert.AttackType, alert.Severity, alert.Details)
	return err
}

func GetRecentAlerts(limit int) ([]models.Alert, error) {
	rows, err := DB.Query(`SELECT id, source_ip, attack_type, severity, details, timestamp FROM alerts ORDER BY timestamp DESC LIMIT $1`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var alerts []models.Alert
	for rows.Next() {
		var a models.Alert
		if err := rows.Scan(&a.ID, &a.SourceIP, &a.AttackType, &a.Severity, &a.Details, &a.Timestamp); err != nil {
			return nil, err
		}
		alerts = append(alerts, a)
	}
	return alerts, nil
}

func GetAlertStats() (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	var totalAlerts int
	err := DB.QueryRow(`SELECT COUNT(*) FROM alerts`).Scan(&totalAlerts)
	if err != nil {
		totalAlerts = 0
	}
	stats["total_alerts"] = totalAlerts

	var highCritical int
	err = DB.QueryRow(`SELECT COUNT(*) FROM alerts WHERE severity IN ('HIGH', 'CRITICAL')`).Scan(&highCritical)
	if err != nil {
		highCritical = 0
	}
	stats["high_critical_alerts"] = highCritical

	var recent24h int
	err = DB.QueryRow(`SELECT COUNT(*) FROM alerts WHERE timestamp >= NOW() - INTERVAL '24 hours'`).Scan(&recent24h)
	if err != nil {
		recent24h = 0
	}
	stats["recent_24h_alerts"] = recent24h

	rows, err := DB.Query(`SELECT attack_type, COUNT(*) FROM alerts GROUP BY attack_type`)
	byType := make(map[string]int)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var at string
			var count int
			if err := rows.Scan(&at, &count); err == nil {
				byType[at] = count
			}
		}
	}
	stats["attacks_by_type"] = byType

	return stats, nil
}

