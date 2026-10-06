package db

import (
	"context"
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

func SaveAlert(alert models.Alert) (models.Alert, error) {
	query := `INSERT INTO alerts (source_ip, attack_type, severity, details) VALUES ($1, $2, $3, $4) RETURNING id, timestamp`
	err := DB.QueryRow(query, alert.SourceIP, alert.AttackType, alert.Severity, alert.Details).Scan(&alert.ID, &alert.Timestamp)
	return alert, err
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
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return alerts, nil
}

func GetAlertStats(ctx context.Context) (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	var totalAlerts int
	if err := DB.QueryRowContext(ctx, `SELECT COUNT(*) FROM alerts`).Scan(&totalAlerts); err != nil {
		return nil, err
	}
	stats["total_alerts"] = totalAlerts

	var highCritical int
	if err := DB.QueryRowContext(ctx, `SELECT COUNT(*) FROM alerts WHERE severity IN ('HIGH', 'CRITICAL')`).Scan(&highCritical); err != nil {
		return nil, err
	}
	stats["high_critical_alerts"] = highCritical

	var recent24h int
	if err := DB.QueryRowContext(ctx, `SELECT COUNT(*) FROM alerts WHERE timestamp >= NOW() - INTERVAL '24 hours'`).Scan(&recent24h); err != nil {
		return nil, err
	}
	stats["recent_24h_alerts"] = recent24h

	rows, err := DB.QueryContext(ctx, `SELECT COALESCE(attack_type, 'UNKNOWN'), COUNT(*) FROM alerts GROUP BY COALESCE(attack_type, 'UNKNOWN')`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	byType := make(map[string]int)
	for rows.Next() {
		var at string
		var count int
		if err := rows.Scan(&at, &count); err != nil {
			return nil, err
		}
		byType[at] = count
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	stats["attacks_by_type"] = byType

	return stats, nil
}

