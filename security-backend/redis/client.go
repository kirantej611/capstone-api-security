package redis

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
)

var Client *redis.Client
var ctx = context.Background()

func InitRedis(addr string) {
	Client = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	_, err := Client.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	log.Println("Connected to Redis successfully")
}

func IncrementRiskScore(ip string, increment float64) (float64, error) {
	key := fmt.Sprintf("risk_score:%s", ip)
	score, err := Client.IncrByFloat(ctx, key, increment).Result()
	if err != nil {
		return 0, err
	}
	// Expire score after 24 hours of inactivity
	Client.Expire(ctx, key, 24*time.Hour)
	return score, nil
}

func BlockIP(ip string) error {
	key := fmt.Sprintf("blocklist:%s", ip)
	// Block for 1 hour
	err := Client.Set(ctx, key, "blocked", 1*time.Hour).Err()
	if err == nil {
		log.Printf("IP %s added to blocklist", ip)
	}
	return err
}

func GetBlocklist() ([]string, error) {
	var ips []string
	iter := Client.Scan(ctx, 0, "blocklist:*", 0).Iterator()
	for iter.Next(ctx) {
		key := iter.Val()
		ips = append(ips, key[10:]) // strip "blocklist:" prefix
	}
	if err := iter.Err(); err != nil {
		return nil, err
	}
	return ips, nil
}
