package api

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

// WebSocket upgrader — allows all origins for dev/demo
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// Hub maintains the set of active WebSocket clients and broadcasts alerts to them.
type Hub struct {
	mu      sync.RWMutex
	clients map[*websocket.Conn]bool
}

// AlertHub is the global singleton hub
var AlertHub = &Hub{
	clients: make(map[*websocket.Conn]bool),
}

// Register adds a new WebSocket client
func (h *Hub) Register(conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.clients[conn] = true
	log.Printf("[ws] Client connected (%d total)", len(h.clients))
}

// Unregister removes a disconnected client
func (h *Hub) Unregister(conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.clients, conn)
	conn.Close()
	log.Printf("[ws] Client disconnected (%d remaining)", len(h.clients))
}

// Broadcast sends a JSON message to all connected WebSocket clients
func (h *Hub) Broadcast(data interface{}) {
	msg, err := json.Marshal(data)
	if err != nil {
		log.Printf("[ws] Marshal error: %v", err)
		return
	}

	h.mu.RLock()
	var failed []*websocket.Conn
	for conn := range h.clients {
		err := conn.WriteMessage(websocket.TextMessage, msg)
		if err != nil {
			log.Printf("[ws] Write error: %v", err)
			failed = append(failed, conn)
		}
	}
	h.mu.RUnlock()

	for _, conn := range failed {
		h.Unregister(conn)
	}
}

// ClientCount returns the number of connected WebSocket clients
func (h *Hub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// HandleWebSocket is the Gin-compatible handler for /ws/alerts
func HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("[ws] Upgrade error: %v", err)
		return
	}

	AlertHub.Register(conn)

	// Keep-alive read loop (detects client disconnect)
	go func() {
		defer AlertHub.Unregister(conn)
		for {
			_, _, err := conn.ReadMessage()
			if err != nil {
				break
			}
		}
	}()
}
