# Resume Automation Platform

An enterprise-grade, AI-powered resume automation platform designed to scale from 100 to 30,000+ concurrent users. Built with event-driven architecture using FastAPI, PostgreSQL, Kafka, and Next.js.

## 🏗️ Architecture Overview

**Current Phase**: Phase 1 Complete - Event-Driven Cell Architecture  
**Status**: 100% complete with production-ready foundation  
**Scale Target**: Designed for 30,000+ users with progressive scaling

### What It Does

- 🔍 **Job Discovery**: AI-powered job board scraping and analysis
- 🤖 **Resume Generation**: Multi-LLM customized resume creation (OpenAI/Anthropic)
- 📊 **Application Tracking**: Complete lifecycle management with analytics
- 🚀 **Auto-Application**: Automated job submissions with success tracking
- 📈 **Learning System**: Improves over time based on outcomes

## 🛠️ Tech Stack

### Backend (Event-Driven Cell Architecture)
- **API**: FastAPI with async PostgreSQL
- **Database**: PostgreSQL with multi-tenant architecture
- **Cache**: Redis for sessions and rate limiting
- **Events**: Kafka for event-driven workflows
- **AI**: Multi-LLM support (OpenAI, Anthropic, Local models)
- **PDF**: LaTeX + Jinja2 for professional resume generation
- **Email**: SMTP integration for user verification

### Frontend (Modern SaaS UI)
- **Framework**: Next.js 15 + TypeScript
- **UI**: Tailwind CSS + shadcn/ui components
- **Features**: Responsive design, dark mode, real-time status dashboard
- **Integration**: Full API proxy with type-safe client
- **Authentication**: Login/register forms with email verification

### Infrastructure
- **Container**: Docker + Docker Compose
- **Orchestration**: Kubernetes ready
- **Service Discovery**: etcd for distributed coordination (Phase 2+)
- **Deployment**: Cell-based architecture for horizontal scaling
- **Logging**: Dual strategy - human-readable console + structured forwarding

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- pdflatex (for PDF generation)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd resume-automation

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Configure poetry to use local venv
poetry env use venv/bin/python
poetry install
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your settings (see Environment Variables section)
```

### 3. Start Services
```bash
# Start PostgreSQL, Redis, Kafka, Zookeeper
docker-compose up -d postgres redis zookeeper kafka

# Run database migrations
poetry run alembic upgrade head
```

### 4. Start Applications
```bash
# Start API server (backend)
./start_api.sh
# OR manually: poetry run uvicorn src.api.main:app --reload

# Start frontend (in new terminal)
cd frontend
npm install
npm run dev
```

### 5. Access Applications
- **Frontend**: http://localhost:3080 (Beautiful SaaS landing page)
- **API Docs**: http://localhost:8048/docs (FastAPI interactive docs)
- **Status Dashboard**: http://localhost:3080/status (Real-time system status)
- **Kafka UI**: http://localhost:9080 (Event stream monitoring)

## 📁 Project Structure

```
resume-automation/
├── src/                    # Backend (Python/FastAPI)
│   ├── api/               # API routes and models
│   ├── core/              # Config, database, events, Kafka
│   ├── agents/            # AI agents (Scraper, Analyzer, Generator, Optimizer)
│   ├── workflows/         # Multi-step job application workflows
│   └── generator/         # Resume generation with LaTeX templates
├── frontend/              # Frontend (Next.js/TypeScript)
│   ├── src/app/          # App router pages
│   ├── src/components/   # Reusable UI components
│   └── src/lib/          # API client and utilities
├── docs/context/         # Architecture and development docs
├── test-scripts/         # Integration test suites
└── docker-compose.yaml  # Local development services
```

## 🏛️ Event-Driven Architecture

### Agent System
- **ScraperAgent**: Discovers jobs from multiple platforms
- **AnalyzerAgent**: Extracts requirements using AI
- **GeneratorAgent**: Creates customized resumes
- **OptimizerAgent**: Improves success rates over time

### Workflow Engine
- **JobApplicationWorkflow**: Complete end-to-end process
- **QuickResumeWorkflow**: Fast resume generation
- **BulkApplicationWorkflow**: Multiple applications in parallel

### Event Flow
```
Job Discovery → Job Analysis → Resume Generation → Application Submission → Response Tracking
```

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Full system integration test
python test-scripts/test_all_endpoints.py

# Resume generation test (includes AI and PDF generation)
python test-scripts/test_resume_generation.py

# LaTeX escaping validation
python test-scripts/test_latex_escaping.py

# Code quality checks
poetry run ruff check .
```

## 🔧 Environment Variables

### Required
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/resume_db
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (for user verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=ResumeAI Platform

# AI Providers (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEFAULT_LLM_PROVIDER=openai

# Service Discovery (Phase 2+)
ETCD_ENDPOINTS=http://localhost:2379
ETCD_USERNAME=
ETCD_PASSWORD=

# CORS
ALLOWED_ORIGINS=["http://localhost:3080", "http://localhost:8000"]
```

### Optional
```bash
# API Configuration
API_V1_PREFIX=/api/v1

# LLM Configuration
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

## 📊 System Status

**Current Implementation (Phase 1)**:
- ✅ **Core Infrastructure**: FastAPI, PostgreSQL, Redis, Kafka all operational
- ✅ **Event System**: Kafka producers/consumers with event schemas
- ✅ **Agent Framework**: 4 specialized agents implemented
- ✅ **Workflow Engine**: Multi-step orchestration with retry logic
- ✅ **Authentication**: JWT with multi-tenant support and usage tiers
- ✅ **Email Verification**: SMTP-based user email verification system
- ✅ **AI Integration**: OpenAI + Anthropic with fallback logic
- ✅ **Resume Generation**: LaTeX templates with PDF compilation
- ✅ **Frontend UI**: Modern Next.js application with status dashboard
- ✅ **API Integration**: Frontend-backend proxy with TypeScript client
- ✅ **Test Utilities**: Test user deletion endpoint for development

**Ready for Phase 2**:
- Go API Gateway for enhanced performance
- etcd for service discovery and distributed configuration
- Worker process separation
- Enhanced monitoring with Prometheus/Grafana
- gRPC internal communication

## 📊 Logging Architecture

### Enterprise Logging Strategy
The platform implements a **dual logging approach** optimized for both human debugging and machine analysis:

**Development & Operations**:
- **Console Output**: Human-readable text format with emoji indicators
- **Docker Debugging**: Plain text logs for `docker logs` readability
- **Local Development**: Descriptive messages with clear error context

**Production & Analytics**:
- **Structured Logs**: JSON format for centralized log aggregation
- **Correlation IDs**: Request tracking across microservices  
- **Log Forwarding**: ELK Stack, Splunk, or cloud logging services
- **Automated Alerts**: Machine-parseable metrics and error patterns

### Configuration
```bash
# Python services (FastAPI backend)
LOG_FORMAT=text              # "text" or "json" 
LOG_LEVEL=info               # "debug", "info", "warn", "error"
LOG_INGEST_ENABLED=false     # Enable centralized log forwarding
LOG_INGEST_URL=http://localhost:9200  # ELK/Elasticsearch endpoint

# Anti-blocking resilience settings
LOG_INGEST_TIMEOUT_MS=2000           # 2 second timeout (fail fast)
LOG_INGEST_QUEUE_SIZE=1000           # Max queued messages
LOG_INGEST_RETRY_ATTEMPTS=3          # Retry failed sends
LOG_INGEST_LATENCY_THRESHOLD_MS=1000 # Circuit breaker threshold
LOG_INGEST_FAILURE_THRESHOLD=5       # Open circuit after N failures
LOG_INGEST_DROP_POLICY=oldest        # Drop policy when queue full

# Go services (API Gateway)
GATEWAY_LOG_FORMAT=text      # "text" or "json"
GATEWAY_LOG_LEVEL=info       # "debug", "info", "warn", "error"
```

### Implementation Details
- **Text Format**: Emoji-enhanced descriptive logs for human readability
- **JSON Format**: Structured fields for automated processing and alerting
- **Runtime Switching**: Environment variables control format without code changes
- **Log Ingestion**: Optional forwarding to ELK Stack, Splunk, or cloud logging
- **Dual Output**: Console logging + centralized aggregation when enabled
- **Anti-Blocking**: Circuit breaker and timeouts prevent slow ingestion from blocking app
- **Resilience**: Queue limits and drop policies ensure stability under load
- **Performance**: Minimal overhead with conditional formatting and async processing

## 🔗 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration with email verification
- `GET /api/v1/auth/verify-email/{token}` - Email verification endpoint
- `POST /api/v1/auth/login` - JWT authentication
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/auth/me/usage` - Usage statistics
- `DELETE /api/v1/auth/test-users` - Delete test users (development only)

### Job Applications
- `GET /api/v1/applications/` - List applications
- `POST /api/v1/applications/` - Create application
- `PATCH /api/v1/applications/{id}` - Update application
- `GET /api/v1/applications/stats/summary` - Analytics

### AI & Generation
- `GET /api/v1/generator/llm-providers` - Available AI providers
- `POST /api/v1/generator/analyze-job` - Job description analysis
- `POST /api/v1/generator/generate-resume` - AI-powered resume creation

### System
- `GET /health` - Service health check
- `GET /docs` - Interactive API documentation

## 🚀 Deployment

### Local Development
```bash
make dev           # Start all services
make test          # Run test suite
make lint          # Code quality checks
```

### Production (Phase 2+)
- Kubernetes manifests in `k8s/` directory
- Terraform infrastructure as code
- GitOps deployment with ArgoCD
- Multi-region scaling support

## 📈 Scaling Architecture

**Phase 1**: Single Cell (100 users) ✅ **CURRENT**  
**Phase 2**: Enhanced Cell + Gateway (1,000 users) - etcd coordination  
**Phase 3**: Multi-Cell Architecture (10,000 users) - etcd service mesh  
**Phase 4**: Global Scale (30,000+ users) - distributed etcd clusters

Each phase builds on the previous without major rewrites. etcd provides the distributed coordination foundation for Phases 2-4.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test-scripts/test_resume_generation.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `docs/context/` for detailed architecture docs
- **Issues**: GitHub Issues for bug reports and feature requests
- **Status**: Visit `/status` endpoint for real-time system health
- **API Docs**: Visit `/docs` for interactive API documentation

---

**Built for Scale**: Designed to handle 30,000+ concurrent users with event-driven architecture and cell-based scaling.