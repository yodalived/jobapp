## 2. claude_context/architecture.md

```markdown
# Resume Automation Architecture

## High-Level Design

User Interface (Web)
↓
API Gateway (FastAPI)
↓
┌────────┴────────┬────────────┬──────────────┐
│                 │            │              │
Job Tracker   Scraper     Generator      ML/Analytics
│                 │            │              │
└────────┬────────┴────────────┴──────────────┘
↓
PostgreSQL / Redis

## Service Responsibilities

### API Service (FastAPI)
- REST endpoints for CRUD operations
- Authentication/authorization
- WebSocket for real-time updates
- Request validation
- Response formatting

### Scraper Service
- LinkedIn Easy Apply (Phase 1)
- Indeed, BuiltIn, Wellfound (Future)
- Job description parsing
- Duplicate detection
- Rate limiting/stealth

### Generator Service  
- Resume customization via LLM
- LaTeX template rendering
- PDF generation
- Version tracking
- Cover letter generation

### Worker Service (Celery)
- Async job processing
- Scheduled scraping
- Email monitoring
- Application submission
- Status updates

### ML Service
- Job relevance scoring
- Success pattern analysis
- Keyword extraction
- RAG implementation
- A/B test analysis

## Data Flow

1. **Job Discovery**

Scraper → Parse JD → Score Relevance → Queue/Auto-apply

2. **Application Flow**
Job URL → Generate Resume → Submit → Track → Learn

3. **Learning Loop**
Outcomes → Analyze Patterns → Update Scoring → Improve Generation

## Technology Choices Rationale

- **FastAPI**: Modern, async, automatic API docs, Pydantic integration
- **PostgreSQL**: JSONB support for flexible metadata, battle-tested
- **Redis**: Fast caching, Celery broker, rate limiting
- **Playwright**: Handles modern JS sites, better than Selenium
- **Celery**: Mature task queue, good monitoring tools
- **SQLAlchemy**: Async support, good migrations with Alembic

## Scaling Considerations

- Horizontal scaling for API (multiple replicas)
- Separate worker pools for different task types
- Redis Sentinel for HA
- PostgreSQL read replicas for analytics
- S3-compatible storage for PDFs
