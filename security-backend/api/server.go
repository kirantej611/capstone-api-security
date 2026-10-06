package api

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"strconv"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/kirantej611/capstone-api-security/security-backend/db"
	rdb "github.com/kirantej611/capstone-api-security/security-backend/redis"
)

func StartServer(port string) {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// CORS — allow the security-dashboard to call us from any origin
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// REST API
	api := r.Group("/api")
	{
		api.GET("/health", healthCheck)
		api.GET("/alerts", getAlerts)
		api.GET("/blocklist", getBlocklist)
		api.GET("/risk/:ip", getRiskScore)
		api.DELETE("/block/:ip", unblockIP)
		api.POST("/block/:ip", blockIP)
		api.GET("/stats", getStats)
		api.GET("/alerts/stream", sseAlerts)
	}

	// WebSocket endpoint (outside /api group — direct path)
	r.GET("/ws/alerts", func(c *gin.Context) {
		HandleWebSocket(c.Writer, c.Request)
	})

	r.Run(":" + port)
}

// GET /api/health
func healthCheck(c *gin.Context) {
	wsClients := AlertHub.ClientCount()
	c.JSON(http.StatusOK, gin.H{
		"status":     "ok",
		"service":    "security-backend",
		"ws_clients": wsClients,
	})
}

// GET /api/alerts?limit=50
func getAlerts(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "50")
	limit, _ := strconv.Atoi(limitStr)
	if limit <= 0 || limit > 500 {
		limit = 50
	}

	alerts, err := db.GetRecentAlerts(limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if alerts == nil {
		c.JSON(http.StatusOK, []gin.H{})
		return
	}
	c.JSON(http.StatusOK, alerts)
}

// GET /api/blocklist
func getBlocklist(c *gin.Context) {
	ips, err := rdb.GetBlocklist()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if ips == nil {
		ips = []string{}
	}
	c.JSON(http.StatusOK, gin.H{"blocked_ips": ips, "count": len(ips)})
}

// GET /api/risk/:ip
func getRiskScore(c *gin.Context) {
	ip := c.Param("ip")
	if net.ParseIP(ip) == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid IP address"})
		return
	}
	ctx := c.Request.Context()

	scoreStr, err := rdb.Client.Get(ctx, fmt.Sprintf("risk_score:%s", ip)).Result()
	if err != nil {
		c.JSON(http.StatusOK, gin.H{"ip": ip, "score": 0, "is_blocked": false})
		return
	}
	score, _ := strconv.ParseFloat(scoreStr, 64)

	blocked, _ := rdb.Client.Exists(ctx, fmt.Sprintf("blocklist:%s", ip)).Result()
	c.JSON(http.StatusOK, gin.H{"ip": ip, "score": score, "is_blocked": blocked > 0})
}

// DELETE /api/block/:ip — unblock an IP
func unblockIP(c *gin.Context) {
	ip := c.Param("ip")
	if net.ParseIP(ip) == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid IP address"})
		return
	}
	ctx := c.Request.Context()

	deleted, err := rdb.Client.Del(ctx, fmt.Sprintf("blocklist:%s", ip)).Result()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if deleted == 0 {
		c.JSON(http.StatusNotFound, gin.H{"message": fmt.Sprintf("IP %s was not blocked", ip)})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "unblocked", "ip": ip})
}

// POST /api/block/:ip — manually block an IP
func blockIP(c *gin.Context) {
	ip := c.Param("ip")
	if net.ParseIP(ip) == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid IP address"})
		return
	}
	if err := rdb.BlockIP(ip); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "blocked", "ip": ip})
}

// GET /api/stats — aggregate attack statistics for the dashboard
func getStats(c *gin.Context) {
	stats, err := db.GetAlertStats(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	blockedIPs, err := rdb.GetBlocklist()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	stats["active_blocked_ips"] = len(blockedIPs)
	stats["ws_clients"] = AlertHub.ClientCount()
	c.JSON(http.StatusOK, stats)
}

// GET /api/alerts/stream — SSE endpoint for browsers that don't support WebSocket
func sseAlerts(c *gin.Context) {
	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.Header().Set("Access-Control-Allow-Origin", "*")

	// Subscribe to alerts via a channel
	alertCh := make(chan string, 10)
	SSESubscribers.Add(alertCh)
	defer SSESubscribers.Remove(alertCh)

	c.Stream(func(w io.Writer) bool {
		select {
		case msg, ok := <-alertCh:
			if !ok {
				return false
			}
			c.SSEvent("alert", msg)
			return true
		case <-c.Request.Context().Done():
			return false
		}
	})
}

// SSESubscribers manages SSE client channels safely with RWMutex
var SSESubscribers = &sseManager{
	channels: make(map[chan string]bool),
}

type sseManager struct {
	mu       sync.RWMutex
	channels map[chan string]bool
}

func (s *sseManager) Add(ch chan string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.channels[ch] = true
}

func (s *sseManager) Remove(ch chan string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.channels, ch)
}

func (s *sseManager) Broadcast(msg string) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	for ch := range s.channels {
		select {
		case ch <- msg:
		default:
			// Skip slow clients whose buffer is full
		}
	}
}
