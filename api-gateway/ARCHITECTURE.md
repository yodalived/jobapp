# API Gateway - Technical Architecture

## Overview

The API Gateway serves as the single entry point for all client requests to the Resume Automation Platform. Built in Go for high performance, it provides cross-cutting concerns like authentication, rate limiting, and observability while maintaining minimal latency overhead.

## Architecture Principles

1. **Performance First**: Sub-10ms overhead for request proxying
2. **Resilient by Design**: Circuit breakers, retries, and fallbacks
3. **Observable**: Comprehensive metrics, logs, and traces
4. **Secure**: JWT validation, rate limiting, and security headers
5. **Simple**: Minimal complexity, easy to understand and modify

## System Context

┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Clients   │────▶│ API Gateway │────▶│ Backend Services│
└─────────────┘     └─────────────┘     └─────────────────┘
                          │
                          ├──────▶ Metrics (Prometheus)
                          ├──────▶ Logs (HTTP Ingestion)
                          └──────▶ Traces (OpenTelemetry)

## Core Components

### 1. Reverse Proxy

The heart of the gateway, using Go's httputil.ReverseProxy:

- Single backend target (Phase 1)
- Multiple backends with load balancing (Phase 2)
- Health-based routing (Phase 2)
- Request/response modification capabilities

### 2. Middleware Stack

Executed in order for each request:

1. **Recovery**: Panic recovery to prevent crashes
2. **Request ID**: Generate unique ID for correlation
3. **Logging**: Structured request/response logging
4. **Metrics**: Prometheus metrics collection
5. **Tracing**: OpenTelemetry span creation
6. **Rate Limiting**: User/IP based limits
7. **Authentication**: JWT validation
8. **Circuit Breaker**: Failure protection
9. **Retry**: Automatic retry logic
10. **Proxy**: Forward to backend

### 3. Configuration System

Layered configuration approach:

- Environment variables (highest priority)
- Configuration file (.env)
- Default values
- Hot reload capability (Phase 2)

### 4. Logging System

Multi-destination resilient logging:

- **Console Handler**: Structured logs to stdout
- **HTTP Handler**: Async batched log shipping
- **Queue Buffer**: Prevent blocking on log failures
- **Drop Policy**: Newest-first when queue full

## Request Flow

### Phase 1: Basic Proxy

Client Request
   │
   ▼
API Gateway (:8000)
   │
   ├─► Health Check (/health)
   │   └─► Direct Response
   │
   └─► All Other Paths
       └─► Proxy to Backend (:8048)

### Phase 2: Full Gateway

Client Request
   │
   ▼
Request ID Generation
   │
   ▼
Rate Limiter
   │
   ├─► Rejected (429 Too Many Requests)
   │
   ▼
JWT Validator
   │
   ├─► Rejected (401 Unauthorized)
   │
   ▼
Circuit Breaker
   │
   ├─► Open (503 Service Unavailable)
   │
   ▼
Load Balancer
   │
   ▼
Backend Service
   │
   ▼
Response Processing
   │
   ▼
Client Response

## Security Architecture

### Authentication

- JWT validation without backend roundtrip
- Public key caching with rotation support
- Claims extraction for request enrichment
- Optional token refresh handling

### Rate Limiting

- Token bucket algorithm
- Redis-backed for distributed limits
- Multiple limit tiers (user, API key, IP)
- Configurable burst handling

### Security Headers

- CORS configuration per route
- Security headers (HSTS, CSP, etc.)
- Request sanitization
- Response filtering

## Performance Optimizations

### Connection Management

- Connection pooling to backends
- Keep-alive management
- Timeout configuration per route
- Circuit breaker integration

### Caching Strategy

- Response caching for idempotent requests
- JWT validation cache
- Service discovery cache
- Health check result caching

### Resource Management

- Bounded goroutine pools
- Memory-aware queue sizing
- Graceful degradation
- Back-pressure handling

## Observability

### Metrics (Prometheus)

Key metrics exposed at /metrics:

- gateway_requests_total: Request count by method, path, status
- gateway_request_duration_seconds: Request latency histogram
- gateway_active_connections: Current active connections
- gateway_rate_limit_exceeded_total: Rate limit violations
- gateway_circuit_breaker_state: Circuit breaker status

### Logging

Structured logs with correlation:

{
 "timestamp": "2024-06-17T10:00:00Z",
 "level": "INFO",
 "request_id": "abc-123",
 "method": "POST",
 "path": "/api/v1/auth/login",
 "status": 200,
 "duration_ms": 45,
 "user_id": "user-456",
 "service": "api-gateway"
}

### Tracing

OpenTelemetry integration:

- Span per request with timing
- Propagation to backend services
- Sampling configuration
- Multiple exporter support

## Deployment Architecture

### Container Structure

FROM golang:1.21-alpine AS builder
# Multi-stage build for minimal image

FROM alpine:latest
# Final image ~15MB

### Kubernetes Integration

- ConfigMap for configuration
- Secret for sensitive values
- HorizontalPodAutoscaler
- PodDisruptionBudget
- NetworkPolicy

### Health Checks

- Liveness: /health/live
- Readiness: /health/ready
- Startup: /health/startup

## High Availability

### Failure Modes

1. **Backend Unavailable**: Circuit breaker opens, fast failures
2. **High Latency**: Request timeouts, retry with backoff
3. **Rate Limit Exceeded**: Graceful degradation, priority queuing
4. **Memory Pressure**: Request shedding, queue drops

### Resilience Patterns

- **Circuit Breaker**: Prevent cascade failures
- **Retry Logic**: Exponential backoff with jitter
- **Timeout Management**: Per-route configuration
- **Bulkhead**: Isolated resource pools
- **Fallback**: Cached or default responses

## Integration Points

### With Backend API

- HTTP/1.1 with keep-alive
- Optional HTTP/2 support
- gRPC support (Phase 3)
- WebSocket proxying

### With Infrastructure

- Prometheus scraping
- StatsD metrics (optional)
- Jaeger/Zipkin tracing
- ELK/Loki logging

## Development Guidelines

### Code Organization

api-gateway/
├── cmd/
│   └── gateway/        # Main application
├── internal/
│   ├── config/         # Configuration
│   ├── middleware/     # HTTP middleware
│   ├── proxy/          # Proxy logic
│   ├── ratelimit/      # Rate limiting
│   └── auth/           # Authentication
├── pkg/
│   ├── health/         # Health checks
│   └── logger/         # Logging utilities
└── tests/
   ├── integration/    # Integration tests
   └── load/          # Load tests

### Performance Guidelines

- Avoid allocations in hot paths
- Use sync.Pool for buffers
- Benchmark middleware impact
- Profile under load
- Monitor goroutine leaks

### Testing Strategy

- Unit tests for each middleware
- Integration tests with mock backend
- Load tests with k6/vegeta
- Chaos tests with toxiproxy
- Security tests with OWASP ZAP

## Future Enhancements

### Phase 3 Additions

- WebAssembly plugins for custom logic
- Request/response transformation
- A/B testing support
- Shadow traffic
- Service mesh integration

### Phase 4 Scaling

- Geographic load balancing
- Edge gateway deployment
- Request coalescing
- Predictive scaling
- ML-based anomaly detection
