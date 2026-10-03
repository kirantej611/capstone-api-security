package main

import (
	"log"

	"github.com/kirantej611/capstone-api-security/security-backend/api"
	"github.com/kirantej611/capstone-api-security/security-backend/config"
	"github.com/kirantej611/capstone-api-security/security-backend/db"
	"github.com/kirantej611/capstone-api-security/security-backend/kafka"
	rdb "github.com/kirantej611/capstone-api-security/security-backend/redis"
)

func main() {
	log.Println("Starting Security Backend (Risk Engine)...")

	cfg := config.LoadConfig()

	// Init Connections
	rdb.InitRedis(cfg.RedisAddr)
	db.InitDB(cfg.PostgresURL)

	// Start Kafka Consumer
	kafka.StartConsumer(cfg)

	// Start REST API
	api.StartServer(cfg.ServerPort)
}
