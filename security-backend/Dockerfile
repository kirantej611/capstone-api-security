# Build stage
FROM golang:1.22-alpine AS builder

# Set the current working directory inside the container
WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download all dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the Go app (statically linked for maximum portability and speed)
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o security-backend .

# Final stage
FROM alpine:latest  

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/

# Copy the pre-built binary file from the previous stage
COPY --from=builder /app/security-backend .

# Expose port
EXPOSE 8082

# Command to run the executable
CMD ["./security-backend"]
