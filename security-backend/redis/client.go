package redis

import (
	"context"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
)

var Client *redis.Client
var ctx = context.Background()

const BlocklistPrefix = "blocklist:ip:"

func BlocklistKey(ip string) string {
	return BlocklistPrefix + ip
}

func RiskScoreKey(ip string) string {
	return "risk_score:" + ip
}

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
	key := RiskScoreKey(ip)
	score, err := Client.IncrByFloat(ctx, key, increment).Result()
	if err != nil {
		return 0, err
	}
	// Expire score after 24 hours of inactivity
	if err := Client.Expire(ctx, key, 24*time.Hour).Err(); err != nil {
		log.Printf("Failed to refresh risk score expiry for %s: %v", ip, err)
	}
	return score, nil
}

func BlockIP(ip string) error {
	// Block for 1 hour
	err := Client.Set(ctx, BlocklistKey(ip), "blocked", 1*time.Hour).Err()
	if err == nil {
		log.Printf("IP %s added to blocklist", ip)
	}
	return err
}

func IsBlocked(ip string) (bool, error) {
	count, err := Client.Exists(ctx, BlocklistKey(ip)).Result()
	return count > 0, err
}

func UnblockIP(ip string) (bool, error) {
	count, err := Client.Del(ctx, BlocklistKey(ip)).Result()
	return count > 0, err
}

func GetBlocklist() ([]string, error) {
	var ips []string
	iter := Client.Scan(ctx, 0, BlocklistPrefix+"*", 0).Iterator()
	for iter.Next(ctx) {
		key := iter.Val()
		ips = append(ips, key[len(BlocklistPrefix):])
	}
	if err := iter.Err(); err != nil {
		return nil, err
	}
	return ips, nil
}
