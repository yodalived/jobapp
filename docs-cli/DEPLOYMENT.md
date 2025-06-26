# Enterprise Deployment Guide

This guide covers deploying the Documentation CLI in enterprise environments with proper configuration management, monitoring, and security.

## 🚀 Deployment Options

### Option 1: Direct Binary Deployment

```bash
# Build for production
go build -ldflags="-s -w" -o docs-cli

# Create deployment directory
mkdir -p /opt/docs-cli/{bin,config,logs,templates}

# Copy files
cp docs-cli /opt/docs-cli/bin/
cp enterprise-config.yaml /opt/docs-cli/config/
cp model-config.yaml /opt/docs-cli/config/
cp components.yaml /opt/docs-cli/config/
cp -r templates/ /opt/docs-cli/templates/

# Set permissions
chmod +x /opt/docs-cli/bin/docs-cli
chown -R docs-cli:docs-cli /opt/docs-cli
```

### Option 2: Docker Deployment

```dockerfile
# Dockerfile.enterprise
FROM golang:1.24-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o docs-cli

FROM alpine:latest

# Install ca-certificates for HTTPS API calls
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user
RUN addgroup -g 1001 -S docs-cli && \
    adduser -u 1001 -S docs-cli -G docs-cli

WORKDIR /app

# Copy binary and configuration
COPY --from=builder /app/docs-cli .
COPY --from=builder /app/enterprise-config.yaml .
COPY --from=builder /app/templates ./templates/

# Create necessary directories
RUN mkdir -p /app/logs /app/cache && \
    chown -R docs-cli:docs-cli /app

USER docs-cli

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./docs-cli --health-check || exit 1

CMD ["./docs-cli"]
```

Build and run:
```bash
docker build -f Dockerfile.enterprise -t docs-cli:enterprise .
docker run -d --name docs-cli \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  -e LOG_LEVEL=info \
  docs-cli:enterprise
```

### Option 3: Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: docs-cli-config
data:
  enterprise-config.yaml: |
    application:
      cache:
        ttl: 2m
        max_size_mb: 50
        max_entries: 1000
      monitoring:
        memory_warning_mb: 500
        memory_critical_mb: 1000
    # ... rest of configuration

---
apiVersion: v1
kind: Secret
metadata:
  name: docs-cli-secrets
type: Opaque
stringData:
  model-config.yaml: |
    openai:
      api_key: "${OPENAI_API_KEY}"
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
    openrouter:
      api_key: "${OPENROUTER_API_KEY}"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-cli
  labels:
    app: docs-cli
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-cli
  template:
    metadata:
      labels:
        app: docs-cli
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: docs-cli
        image: docs-cli:enterprise
        ports:
        - containerPort: 8080
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: ENABLE_METRICS
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: secrets
          mountPath: /app/secrets
          readOnly: true
        livenessProbe:
          exec:
            command:
            - ./docs-cli
            - --health-check
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - ./docs-cli
            - --health-check
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: docs-cli-config
      - name: secrets
        secret:
          secretName: docs-cli-secrets
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

## 🔧 Configuration Management

### Environment-Specific Configurations

**Development (enterprise-config.dev.yaml)**:
```yaml
application:
  cache:
    ttl: 30s  # Shorter for development
    max_size_mb: 10
  monitoring:
    memory_warning_mb: 100
    memory_critical_mb: 200
  resilience:
    retry:
      max_attempts: 1  # Fail fast in dev

providers:
  anthropic:
    timeout: 10s  # Shorter timeouts
  openai:
    timeout: 15s
```

**Production (enterprise-config.prod.yaml)**:
```yaml
application:
  cache:
    ttl: 10m  # Longer for production
    max_size_mb: 100
  monitoring:
    memory_warning_mb: 800
    memory_critical_mb: 1500
  resilience:
    retry:
      max_attempts: 5  # More resilient

providers:
  anthropic:
    timeout: 60s  # More patient
  openai:
    timeout: 90s
```

### Configuration Validation

Create a validation script:
```bash
#!/bin/bash
# validate-config.sh

echo "Validating enterprise configuration..."

# Check required files exist
required_files=("enterprise-config.yaml" "model-config.yaml" "components.yaml")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

# Validate YAML syntax
for file in *.yaml; do
    if ! yq eval '.' "$file" > /dev/null 2>&1; then
        echo "❌ Invalid YAML syntax in: $file"
        exit 1
    fi
done

# Check API keys are not hardcoded
if grep -r "sk-" --include="*.yaml" .; then
    echo "❌ Found hardcoded API keys in configuration files"
    exit 1
fi

# Validate go build
if ! go build -o /tmp/docs-cli-test .; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Configuration validation passed"
```

## 📊 Monitoring & Observability

### Health Checks

Add health check endpoint to main.go:
```go
var healthCmd = &cobra.Command{
    Use:   "health",
    Short: "Health check endpoint",
    Run: func(cmd *cobra.Command, args []string) {
        config, err := configManager.LoadConfig()
        if err != nil {
            fmt.Println("❌ Configuration load failed")
            os.Exit(1)
        }
        
        // Check memory usage
        stats := GetMemoryStats()
        monitoringConfig := config.Application.Monitoring
        if stats.AllocMB >= monitoringConfig.MemoryCriticalMB {
            fmt.Println("❌ Memory usage critical")
            os.Exit(1)
        }
        
        // Check API connectivity
        // ... provider health checks
        
        fmt.Println("✅ Health check passed")
    },
}
```

### Metrics Collection

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'docs-cli'
    static_configs:
      - targets: ['docs-cli:8080']
    metrics_path: /metrics
    scrape_interval: 30s
```

### Log Aggregation

For ELK Stack:
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/docs-cli/logs/*.log
  fields:
    service: docs-cli
    environment: production
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "docs-cli-%{+yyyy.MM.dd}"
```

## 🔒 Security Hardening

### API Key Management

**Using HashiCorp Vault**:
```bash
# Store API keys in Vault
vault kv put secret/docs-cli \
  openai_key="sk-..." \
  anthropic_key="sk-ant-..." \
  openrouter_key="sk-or-..."

# Retrieve in application
vault kv get -field=openai_key secret/docs-cli
```

**Using Kubernetes Secrets**:
```bash
# Create secret from files
kubectl create secret generic docs-cli-api-keys \
  --from-literal=openai-key="sk-..." \
  --from-literal=anthropic-key="sk-ant-..." \
  --from-literal=openrouter-key="sk-or-..."
```

### Network Security

**Firewall Rules**:
```bash
# Allow only necessary outbound connections
iptables -A OUTPUT -p tcp --dport 443 -m owner --uid-owner docs-cli -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -m owner --uid-owner docs-cli -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner docs-cli -j DROP
```

**Network Policies (Kubernetes)**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: docs-cli-netpol
spec:
  podSelector:
    matchLabels:
      app: docs-cli
  policyTypes:
  - Egress
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### Resource Limits

**systemd Service (Linux)**:
```ini
# /etc/systemd/system/docs-cli.service
[Unit]
Description=Documentation CLI Service
After=network.target

[Service]
Type=simple
User=docs-cli
Group=docs-cli
WorkingDirectory=/opt/docs-cli
ExecStart=/opt/docs-cli/bin/docs-cli daemon
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/docs-cli/logs /opt/docs-cli/cache

# Resource limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

## 🚨 Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/docs-cli/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r /opt/docs-cli/config "$BACKUP_DIR/"

# Backup cache (if needed)
cp -r /opt/docs-cli/cache "$BACKUP_DIR/"

# Backup logs
cp -r /opt/docs-cli/logs "$BACKUP_DIR/"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### Recovery Procedures

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop service
systemctl stop docs-cli

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restore configuration
cp -r "$TEMP_DIR"/*/config/* /opt/docs-cli/config/

# Validate configuration
if /opt/docs-cli/bin/docs-cli --validate-config; then
    systemctl start docs-cli
    echo "✅ Recovery completed successfully"
else
    echo "❌ Configuration validation failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"
```

## 📈 Performance Tuning

### Go Runtime Optimization

```bash
# Environment variables for production
export GOGC=100                    # GC percentage
export GOMEMLIMIT=1GiB            # Memory limit
export GOMAXPROCS=2               # CPU cores
export GODEBUG=gctrace=1          # GC tracing (for tuning)
```

### Configuration Tuning

**High-Load Environment**:
```yaml
application:
  cache:
    ttl: 30m              # Longer cache for stability
    max_size_mb: 200      # Larger cache
    max_entries: 5000     # More entries
    cleanup_interval: 5m  # Less frequent cleanup
  
  resilience:
    retry:
      max_attempts: 3
      initial_delay: 500ms
      max_delay: 10s
    circuit_breaker:
      failure_threshold: 10  # More tolerant
      timeout: 60s
```

### Database Connection Pooling

If adding database support:
```yaml
database:
  max_open_conns: 25
  max_idle_conns: 5
  conn_max_lifetime: 5m
  conn_max_idle_time: 2m
```

## 🔍 Troubleshooting

### Common Production Issues

**Memory Leaks**:
```bash
# Monitor memory usage
watch -n 5 'ps aux | grep docs-cli'

# Generate heap profile
go tool pprof http://localhost:8080/debug/pprof/heap
```

**API Rate Limiting**:
```bash
# Check rate limit headers in logs
grep "rate.*limit" /opt/docs-cli/logs/app.log

# Adjust retry configuration
# Increase delays and reduce attempts
```

**Configuration Issues**:
```bash
# Validate configuration
./docs-cli --validate-config

# Test with minimal config
./docs-cli --config-file minimal-config.yaml
```

### Log Analysis

```bash
# Find errors
grep -i error /opt/docs-cli/logs/*.log | tail -20

# API call performance
grep "API call completed" /opt/docs-cli/logs/*.log | \
  grep -o "duration_ms\":[0-9]*" | \
  cut -d: -f2 | \
  sort -n

# Cache hit rate
grep "cache_metrics" /opt/docs-cli/logs/*.log | \
  tail -1 | \
  jq '.cache_metrics.hit_ratio'
```

This deployment guide ensures enterprise-grade deployment with proper security, monitoring, and operational procedures.