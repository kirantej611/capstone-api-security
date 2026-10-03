# Build stage — compiles the Go binary statically
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cache)
COPY go.mod go.sum ./
RUN go mod download

# Copy source and build a fully static binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -ldflags="-s -w" -o security-backend .

# Final stage — reuse golang:1.22-alpine (already cached); strip to just the binary
FROM golang:1.22-alpine

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/security-backend .

EXPOSE 8082

CMD ["./security-backend"]
