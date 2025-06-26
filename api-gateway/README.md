# API Gateway

## Overview

The API Gateway is a high-performance entry point for all client requests to the Resume Automation Platform. Built in Go, it provides authentication, rate limiting, observability, and resilience patterns while maintaining sub-10ms latency overhead.

## Architecture

This gateway implements a middleware-based request processing pipeline:

1. **Request Processing Layer**: Recovery, request ID, logging
2. **Security Layer**: JWT validation, rate limiting, security headers
3. **Resilience Layer**: Circuit breakers, retries, timeouts
4. **Routing Layer**: Load balancing, health-based routing

## Core Components

### 1. Reverse Proxy
- **HTTP Proxy**: Built on Go's httputil.ReverseProxy
- **Load Balancing**: Round-robin with health checks
- **Connection Pooling**: Reusable backend connections
- **Protocol Support**: HTTP/1.1, HTTP/2, WebSocket

### 2. Security Pipeline
- **JWT Validation**: Local validation without backend calls
- **Rate Limiting**: Token bucket with Redis backend
- **Request Sanitization**: Input validation and filtering
- **Security Headers**: CORS, HSTS, CSP configuration

### 3. Resilience Features
- **Circuit Breaker**: Fast failure on backend issues
- **Retry Logic**: Exponential backoff with jitter
- **Timeout Management**: Per-route configuration
- **Bulkhead Pattern**: Isolated resource pools

### 4. Observability Stack
- **Structured Logging**: JSON logs with correlation IDs
- **Metrics Collection**: Prometheus-compatible metrics
- **Distributed Tracing**: OpenTelemetry integration
- **Health Endpoints**: Liveness and readiness probes

## Request Flow

[Client] → [Gateway] → [Middleware Stack] → [Backend Service]
               ↓
         [Metrics/Logs/Traces]

## Key Features

- **Performance**: Sub-10ms proxy overhead
- **Security**: JWT validation and rate limiting
- **Reliability**: Circuit breakers and retries
- **Observability**: Full request tracing and metrics
- **Scalability**: Horizontal scaling ready

## Configuration

All configuration via environment variables:
- GATEWAY_PORT: Listen port (default: 8000)
- GATEWAY_BACKEND_TARGET: Backend URL
- LOG_FORMAT: json or text
- LOG_LEVEL: DEBUG, INFO, WARN, ERROR
- Rate limiting, circuit breaker settings (see SETUP.md)

## Getting Started

See /implementation/SETUP.md for detailed setup instructions.

## Directory Structure

api-gateway/
├── README.md                    # This file
├── implementation/             
│   ├── SETUP.md               # Setup instructions
│   ├── ARCHITECTURE.md        # Detailed architecture
│   └── DEVELOPMENT.md         # Development guide
├── cmd/
│   └── gateway/               # Main application
├── internal/
│   ├── config/                # Configuration management
│   ├── middleware/            # HTTP middleware
│   ├── proxy/                 # Proxy logic
│   └── ratelimit/             # Rate limiting
├── pkg/
│   ├── health/                # Health check handlers
│   └── logger/                # Logging utilities
└── tests/
   ├── integration/           # Integration tests
   ├── load/                  # Load testing scripts
   └── unit/                  # Unit tests
