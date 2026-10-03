package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	KafkaBrokers  string
	KafkaTopic    string
	RedisAddr     string
	PostgresURL   string
	ServerPort    string
	BlockThreshold float64
}

func LoadConfig() Config {
	err := godotenv.Load()
	if err != nil {
		log.Println("No .env file found or error reading it, using system environment variables")
	}

	threshold, _ := strconv.ParseFloat(getEnv("BLOCK_THRESHOLD", "80.0"), 64)

	return Config{
		KafkaBrokers:   getEnv("KAFKA_BROKERS", "kafka:29092"),
		KafkaTopic:     getEnv("KAFKA_TOPIC", "ml-predictions"),
		RedisAddr:      getEnv("REDIS_ADDR", "redis:6379"),
		PostgresURL:    getEnv("POSTGRES_URL", "postgres://admin:password@postgres:5432/capstone_db?sslmode=disable"),
		ServerPort:     getEnv("PORT", "8082"),
		BlockThreshold: threshold,
	}
}

func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}
