# API Component Architecture

## Overview

The API component serves as the primary interface layer for the Resume Automation Platform, implementing a RESTful API using FastAPI. It provides authentication, job application management, resume generation orchestration, and file handling capabilities while maintaining multi-tenant isolation and preparing for horizontal scaling.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                      (Phase 2+ - Go)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      API Component                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  FastAPI Application                │    │
│  │  ┌─────────┐  ┌────────────┐┌──────────────────┐    │    │
│  │  │ Routers │  │Dependencies││    Middleware    │    │    │
│  │  └────┬────┘  └─────┬──────┘└────────┬─────────┘    │    │
│  │       │             │                │              │    │
│  │  ┌────┴─────────────┴────────────────┴──────────┐   │    │
│  │  │              Request Pipeline                │   │    │
│  │  └───────────────────┬──────────────────────────┘   │    │
│  └──────────────────────┼──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────┼───────────────────────────────┐   │
│  │                   Services Layer                     │   │
│  │  ┌─────────┐  ┌──────┴────┐  ┌─────────────────┐     │   │
│  │  │  Auth   │  │Application│  │    Generator    │     │   │
│  │  │ Service │  │  Service  │  │     Service     │     │   │
│  │  └────┬────┘  └─────┬─────┘  └────────┬────────┘     │   │
│  └───────┼─────────────┼─────────────────┼──────────────┘   │
│          │             │                 │                  │
└──────────┼─────────────┼─────────────────┼──────────────────┘
           │             │                 │
    ┌──────┴───┐   ┌─────┴───┐       ┌─────┴───┐
    │PostgreSQL│   │  Redis  │       │  Kafka  │
    └──────────┘   └─────────┘       └─────────┘
```

## Component Relationships

### Internal Dependencies
- **Database Layer**: Async SQLAlchemy for PostgreSQL interactions
- **Auth System**: JWT-based authentication with multi-tenant isolation
- **Event Bus**: Kafka integration for asynchronous workflows
- **Cache Layer**: Redis for session management and rate limiting
- **File Service**: Abstracted storage backend for resume/document handling

### External Integrations
- **LLM Providers**: OpenAI and Anthropic for AI-powered features
- **Frontend**: Next.js application via CORS-enabled REST API
- **Email Service**: SMTP integration for user verification
- **Storage Backends**: Local/MinIO/S3/Azure for file storage

## Data Flow

### 1. Authentication Flow
```
User Request → OAuth2PasswordBearer → JWT Validation → User Context
     ↓                                       ↓
   Login → Password Hash Verification → Token Generation
     ↓
Email Verification → Token Storage → Account Activation
```

### 2. Job Application Flow
```
Create Application → Validate User Limits → Store in DB
        ↓                                        ↓
   Emit Event → Kafka → ScraperAgent → AnalyzerAgent
        ↓
  Update Status → Notify User → Track Analytics
```

### 3. Resume Generation Flow
```
Generate Request → Check Verification Status → Check Usage Limits
        ↓                                              ↓
   Analyze Job → LLM Service → Generate LaTeX → Compile PDF
        ↓                                              ↓
  Store File → Update Usage Count → Return Download URL
```

## Key Design Decisions

### 1. Async-First Architecture
**Decision**: Use async/await throughout with AsyncSession for database operations.
**Rationale**: 
- Better performance for I/O-bound operations
- Natural fit with FastAPI's async capabilities
- Scales better under concurrent load
- Prepares for high-throughput Phase 3/4 requirements

### 2. Dependency Injection Pattern
**Decision**: Heavy use of FastAPI's dependency injection system.
**Rationale**:
- Clean separation of concerns
- Easy testing and mocking
- Consistent authentication/authorization
- Database session management per request

### 3. Multi-Tenant by Design
**Decision**: Row-level security with user_id foreign keys.
**Rationale**:
- Simpler than database-per-tenant
- Cost-effective for SaaS model
- Easy to implement with SQLAlchemy
- Can migrate to schema-per-tenant later if needed

### 4. Tiered Authorization
**Decision**: Subscription tiers embedded in JWT tokens.
**Rationale**:
- Fast authorization without database lookups
- Feature gating at API level
- Clear upgrade paths for users
- Supports freemium business model

## Patterns Used

### 1. Repository Pattern (Implicit)
While not explicitly implemented, the routers act as repositories:
```python
# Router handles data access patterns
@router.get("/applications/")
async def list_applications(db: AsyncSession = Depends(get_db)):
    # Repository-like data access
```

### 2. Chain of Responsibility
Authentication pipeline implements this pattern:
```python
get_current_user → get_current_active_user → get_verified_user → check_resume_generation_limit
```

### 3. Factory Pattern
LLM service selection uses factory pattern:
```python
LLMService.get_provider(provider_name) → OpenAIProvider | AnthropicProvider
```

### 4. Event-Driven Architecture
All state changes emit events:
```python
Create Application → emit("application.created") → Trigger Workflows
```

## Scaling Considerations

### Phase 1 (Current - 100 users)
- Single FastAPI instance
- Local file storage
- Simple in-memory rate limiting
- Direct database connections

### Phase 2 (1,000 users)
- Go API Gateway for performance
- Redis-based rate limiting
- Connection pooling
- Separate worker processes

### Phase 3 (10,000 users)
- Multiple API instances behind load balancer
- Distributed rate limiting
- Read replicas for queries
- Service mesh integration

### Phase 4 (30,000+ users)
- Geographic distribution
- Edge caching
- GraphQL federation option
- Circuit breakers and bulkheads

## Security Considerations

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with expiration
- **Password Hashing**: bcrypt with salt
- **Email Verification**: Required for full access
- **Role-Based Access**: Subscription tiers control features

### API Security
- **CORS Configuration**: Whitelist allowed origins
- **Rate Limiting**: Per-user and per-tier limits
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy

### Data Protection
- **Multi-Tenant Isolation**: user_id filtering on all queries
- **Sensitive Data**: No PII in logs or error messages
- **File Access**: Signed URLs with expiration
- **Audit Trail**: Event log for all state changes

## Technology Stack

### Core Framework
- **FastAPI**: Modern, fast, async Python framework
  - Automatic OpenAPI documentation
  - Built-in validation with Pydantic
  - Excellent async support
  - Strong typing throughout

### Database Layer
- **PostgreSQL**: Primary data store
  - ACID compliance for financial data
  - JSONB for flexible metadata
  - Full-text search capabilities
  - Proven scalability

- **SQLAlchemy 2.0**: ORM with async support
  - Type-safe queries
  - Migration support via Alembic
  - Connection pooling
  - Complex query optimization

### Caching & Sessions
- **Redis**: In-memory data structure store
  - Session storage
  - Rate limiting counters
  - Temporary file URLs
  - Event queue backup

### Event Streaming
- **Kafka**: Distributed event streaming
  - Reliable event delivery
  - Horizontal scalability
  - Event replay capability
  - Decoupled architecture

## Future Architecture Plans

### Phase 2 Enhancements
1. **Go API Gateway**
   - High-performance request routing
   - Built-in rate limiting
   - Request/response transformation
   - Protocol translation (HTTP/2, gRPC)

2. **Service Decomposition**
   - Extract resume generation to microservice
   - Separate authentication service
   - Independent file service

### Phase 3 Evolution
1. **GraphQL Layer**
   - Efficient data fetching
   - Real-time subscriptions
   - Federation for microservices
   - Better mobile app support

2. **CQRS Implementation**
   - Separate read/write models
   - Event sourcing for audit trail
   - Optimized query performance
   - Better scalability

### Phase 4 Global Scale
1. **Edge Computing**
   - CDN for static assets
   - Edge workers for auth
   - Regional API endpoints
   - Reduced latency globally

2. **Service Mesh**
   - Istio for traffic management
   - Automatic retries and circuit breaking
   - Distributed tracing
   - Security policies

## API Design Principles

### RESTful Standards
- Consistent URL patterns: `/api/v1/{resource}/{id}/{action}`
- Proper HTTP verbs: GET, POST, PATCH, DELETE
- Status codes: 2xx success, 4xx client error, 5xx server error
- HATEOAS where appropriate

### Response Consistency
```python
# Success Response
{
    "data": {...},
    "meta": {
        "page": 1,
        "total": 100
    }
}

# Error Response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [...]
    }
}
```

### Versioning Strategy
- URL-based versioning: `/api/v1/`, `/api/v2/`
- Deprecation notices in headers
- Backward compatibility for 2 versions
- Clear migration guides

## Performance Optimizations

### Current Optimizations
- Async database queries
- Eager loading for relationships
- Indexed database queries
- Pydantic model caching

### Future Optimizations
- Query result caching
- Database connection pooling
- Batch API operations
- GraphQL query complexity analysis

## Monitoring & Observability

### Current State
- Basic health checks
- Console logging
- Error tracking via exceptions

### Future State
- Prometheus metrics
- Distributed tracing (Jaeger)
- Structured logging (JSON)
- APM integration (DataDog/New Relic)

## Conclusion

The API component serves as the critical interface layer for the Resume Automation Platform, implementing modern patterns and preparing for massive scale. Its event-driven architecture, multi-tenant design, and async-first approach provide a solid foundation for growth from 100 to 30,000+ users without major rewrites. The clear separation of concerns, comprehensive security measures, and thoughtful technology choices ensure the platform can evolve gracefully through each scaling phase.
