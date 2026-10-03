package api

import (
	"context"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/kirantej611/capstone-api-security/security-backend/db"
	rdb "github.com/kirantej611/capstone-api-security/security-backend/redis"
)

func StartServer(port string) {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// CORS — allow the security-dashboard (Member 4) to call us from any origin
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	api := r.Group("/api")
	{
		api.GET("/health",    healthCheck)
		api.GET("/alerts",    getAlerts)
		api.GET("/blocklist", getBlocklist)
		api.GET("/risk/:ip",  getRiskScore)
		api.DELETE("/block/:ip", unblockIP)
	}

	r.Run(":" + port)
}

// GET /api/health
func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok", "service": "security-backend"})
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

// GET /api/risk/:ip — returns the current cumulative risk score for an IP
func getRiskScore(c *gin.Context) {
	ip := c.Param("ip")
	ctx := context.Background()

	scoreStr, err := rdb.Client.Get(ctx, fmt.Sprintf("risk_score:%s", ip)).Result()
	if err != nil {
		c.JSON(http.StatusOK, gin.H{"ip": ip, "score": 0, "is_blocked": false})
		return
	}
	score, _ := strconv.ParseFloat(scoreStr, 64)

	// Check if currently blocked
	blocked, _ := rdb.Client.Exists(ctx, fmt.Sprintf("blocklist:%s", ip)).Result()

	c.JSON(http.StatusOK, gin.H{
		"ip":         ip,
		"score":      score,
		"is_blocked": blocked > 0,
	})
}

// DELETE /api/block/:ip — manually unblock an IP (admin action)
func unblockIP(c *gin.Context) {
	ip := c.Param("ip")
	ctx := context.Background()

	deleted, err := rdb.Client.Del(ctx, fmt.Sprintf("blocklist:%s", ip)).Result()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if deleted == 0 {
		c.JSON(http.StatusNotFound, gin.H{"message": fmt.Sprintf("IP %s was not blocked", ip)})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": fmt.Sprintf("IP %s unblocked successfully", ip)})
}
