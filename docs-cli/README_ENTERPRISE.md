# Documentation CLI - Enterprise Edition

A production-ready CLI tool for automated documentation generation using AI, built with enterprise software engineering best practices.

## 🏗️ Enterprise Architecture

### Configuration-Driven Design
- **Zero Hardcoded Values**: All configuration externalized to `enterprise-config.yaml`
- **Environment-Specific**: Easy deployment across dev/staging/production
- **Hot-Reloadable**: Configuration changes without code rebuilds

### Modular Package Structure
```
pkg/
├── config/           # Enterprise configuration management
│   └── enterprise_config.go
├── scanner/          # File scanning with interfaces
│   └── file_scanner.go
├── templates/        # Template processing system
│   └── processor.go
└── documentation/    # Documentation generation service
    └── service.go
```

### Enterprise Patterns Implemented
- **Dependency Injection**: Clean interfaces and testable components
- **Circuit Breakers**: Resilient API calls with failure handling
- **Enterprise Caching**: LRU cache with metrics and size limits
- **Structured Logging**: Comprehensive logging with context fields
- **Memory Monitoring**: Resource usage tracking and automatic GC
- **Input Validation**: Security-first approach to data handling
- **Cost Optimization**: AI model cost management and token estimation

## 🚀 Quick Start

### Prerequisites
- Go 1.24+ 
- Valid API keys for AI providers (OpenAI, Anthropic, OpenRouter)

### Installation
```bash
git clone <repository>
cd docs-cli
go build -o docs-cli
```

### Configuration
1. Copy and customize the enterprise configuration:
```bash
cp enterprise-config.yaml.example enterprise-config.yaml
```

2. Set your API keys in `model-config.yaml`:
```yaml
openai:
  api_key: "your-openai-key"
anthropic:
  api_key: "your-anthropic-key"
openrouter:
  api_key: "your-openrouter-key"
```

3. Define your components in `components.yaml`:
```yaml
components:
  - name: "api"
    path: "src/api"
    type: "service"
    description: "REST API service"
```

## 📚 Usage

### Generate Documentation
```bash
# Generate README for specific component
./docs-cli create README api

# Generate all documentation for all components
./docs-cli create all all

# Generate with thinking enabled (for supported models)
./docs-cli create README api --think

# Update all existing documentation
./docs-cli update

# Generate with context chaining (conversation continuity)
./docs-cli context
```

### List Components
```bash
./docs-cli list
```

### Generate Status Page
```bash
./docs-cli status
```

## ⚙️ Enterprise Configuration

### Provider Configuration
All AI providers are fully configurable:

```yaml
providers:
  anthropic:
    api_url: "https://api.anthropic.com/v1/messages"
    timeout: 30s
    temperature_range:
      min: 0.0
      max: 1.0
  
  openai:
    api_url: "https://api.openai.com/v1/chat/completions"
    timeout: 60s
    temperature_range:
      min: 0.0
      max: 2.0
```

### Performance Tuning
```yaml
application:
  cache:
    ttl: 2m
    max_size_mb: 50
    max_entries: 1000
  
  monitoring:
    memory_warning_mb: 500
    memory_critical_mb: 1000
  
  resilience:
    retry:
      max_attempts: 3
      initial_delay: 1s
      backoff_multiplier: 2.0
```

### Cost Optimization
```yaml
cost_optimization:
  token_estimation_ratio: 0.25
  complexity_thresholds:
    simple: 2000
    complex: 10000
  pricing:
    anthropic:
      sonnet4:
        input_cost: 0.015
        output_cost: 0.075
```

## 🔧 Advanced Features

### Thinking Models Support
Enable deep reasoning for compatible models:
```bash
./docs-cli create ARCHITECTURE api --think
```

Supported thinking models:
- DeepSeek-R1 (via OpenRouter)
- OpenAI o1/o3 series
- Anthropic Claude 4 (when available)

### Context Chaining
Generate documentation with conversation continuity:
```bash
./docs-cli context
```

This generates documents in sequence (ARCHITECTURE → README → SETUP → CHECKLIST) where each document builds upon the previous ones.

### File Scanning Configuration
```yaml
file_scanning:
  max_depth: 3
  default_file_limit: 10
  file_priorities:
    ".go": 10
    ".py": 9
    ".ts": 8
```

## 🏢 Enterprise Features

### Monitoring & Observability
- **Memory Usage Monitoring**: Automatic tracking with thresholds
- **Cache Performance Metrics**: Hit ratios, size tracking, eviction stats  
- **API Call Logging**: Structured logs with context and timing
- **Circuit Breaker Status**: Real-time failure tracking

### Security
- **Input Validation**: All inputs sanitized and validated
- **No Secrets in Code**: API keys externalized to configuration
- **Rate Limiting**: Prevent API abuse and cost overruns
- **Memory Limits**: Prevent resource exhaustion

### Resilience
- **Circuit Breakers**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff with configurable attempts
- **Timeout Handling**: Provider-specific timeout configurations
- **Graceful Degradation**: Fallback mechanisms for failures

### Performance
- **LRU Caching**: Intelligent caching of API responses
- **Memory Management**: Automatic garbage collection triggers
- **Token Estimation**: Cost prediction before API calls
- **File Scanning Optimization**: Configurable depth and limits

## 🧪 Development

### Architecture Principles
- **Single Responsibility**: Each package has one clear purpose
- **Dependency Injection**: Interfaces enable testing and extensibility
- **Configuration Over Convention**: Everything is configurable
- **Fail Fast**: Early validation and clear error messages

### Testing
```bash
# Run tests
go test ./...

# Run with coverage
go test -cover ./...

# Test specific package
go test ./pkg/scanner
```

### Adding New Providers
1. Implement the `ModelProvider` interface
2. Add configuration schema to `enterprise-config.yaml`
3. Register the provider in the factory
4. Add tests and documentation

## 📊 Cost Management

The tool includes comprehensive cost optimization:

- **Token Estimation**: Preview costs before generation
- **Model Selection**: Automatic optimal model selection
- **Prompt Compression**: Intelligent content reduction
- **Usage Tracking**: Detailed cost reporting per provider

## 🔍 Troubleshooting

### Common Issues

**Configuration Errors**:
```bash
# Validate configuration
./docs-cli --help  # Will show config errors
```

**Memory Issues**:
- Adjust `memory_critical_mb` in enterprise-config.yaml
- Enable more aggressive garbage collection

**API Failures**:
- Check circuit breaker status in logs
- Verify API keys and rate limits
- Review timeout configurations

### Logging
Enable debug logging:
```bash
export LOG_LEVEL=debug
./docs-cli create README api
```

## 📈 Production Deployment

### Docker Deployment
```dockerfile
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o docs-cli

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/docs-cli .
COPY --from=builder /app/enterprise-config.yaml .
COPY --from=builder /app/templates ./templates/
CMD ["./docs-cli"]
```

### Environment Variables
```bash
# Override configuration file location
export ENTERPRISE_CONFIG_PATH="/etc/docs-cli/config.yaml"

# Set log level
export LOG_LEVEL="info"

# Enable metrics
export ENABLE_METRICS="true"
```

### Health Checks
The application exposes health check endpoints for monitoring:
- Memory usage within limits
- Cache performance metrics
- API provider connectivity

## 🤝 Contributing

1. Follow the established architecture patterns
2. Add comprehensive tests for new features
3. Update configuration schemas
4. Maintain backward compatibility
5. Document enterprise considerations

## 📄 License

Enterprise documentation CLI tool with production-ready architecture.