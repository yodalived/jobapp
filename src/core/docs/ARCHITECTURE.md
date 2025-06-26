# ARCHITECTURE.md - Core Service Layer

## Overview

The Core service layer is the foundational component of the Resume Automation Platform, providing essential infrastructure services that all other components depend on. It implements critical cross-cutting concerns including authentication, database connectivity, event streaming, storage abstraction, and email services.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────────┤
│                          Core Services                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │    Auth     │  │   Database   │  │   Event System      │  │
│  │  - JWT      │  │  - Async PG  │  │  - Kafka Producer   │  │
│  │  - Bcrypt   │  │  - Pooling   │  │  - Event Schemas    │  │
│  │  - Tiers    │  │  - Migration │  │  - Event Bus        │  │
│  └─────────────┘  └──────────────┘  └─────────────────────┘  │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │   Storage   │  │    Email     │  │   Configuration     │  │
│  │  - Multi-   │  │  - SMTP      │  │  - Pydantic        │  │
│  │    Backend  │  │  - Templates │  │  - Environment     │  │
│  │  - Dynamic  │  │  - Async     │  │  - Validation      │  │
│  └─────────────┘  └──────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼────┐      ┌──────▼─────┐
              │PostgreSQL │      │   Kafka    │
              └──────────┘      └────────────┘
```

## Component Relationships

### Internal Dependencies
```
config.py
    ↓
database.py ←→ auth.py
    ↓           ↓
storage/* ← email.py
    ↓
events.py → kafka_client.py → event_bus.py
```

### External Interactions
- **API Layer**: Provides database sessions, authentication, and core services
- **Agents**: Use event bus for publishing workflow events
- **Workflows**: Consume events and use storage/email services
- **Frontend**: Authenticates through JWT tokens, receives emails

## Data Flow

### Authentication Flow
```
1. User Login Request
   ↓
2. auth.authenticate_user() validates credentials
   ↓
3. create_access_token() generates JWT
   ↓
4. JWT returned to client
   ↓
5. Subsequent requests include JWT
   ↓
6. decode_access_token() validates and extracts user info
```

### Event Flow
```
1. Business Event Occurs (e.g., resume generated)
   ↓
2. Event published to event_bus.publish()
   ↓
3. KafkaEventProducer serializes and sends to Kafka
   ↓
4. Topic partitioned by user_id for ordering
   ↓
5. KafkaEventConsumer receives and deserializes
   ↓
6. Registered handlers process event asynchronously
```

### Storage Flow
```
1. File Operation Request
   ↓
2. StorageManager routes to appropriate backend
   ↓
3. Backend performs operation (save/retrieve/delete)
   ↓
4. Metadata tracked for audit/analytics
   ↓
5. Optional: Storage events emitted for workflows
```

## Key Design Decisions

### 1. Async-First Architecture
**Decision**: Use async/await throughout with asyncpg
**Rationale**: 
- Handles high concurrency without thread overhead
- Natural fit for I/O-bound operations
- Integrates seamlessly with FastAPI
- Enables non-blocking database queries

### 2. Multi-Backend Storage with Dynamic Loading
**Decision**: Abstract storage with pluggable backends loaded dynamically
**Rationale**:
- Zero-downtime backend switching via configuration
- Support for local development and cloud production
- Vendor independence (MinIO → S3 → Azure)
- Graceful handling of missing dependencies

### 3. Event-Driven from Day One
**Decision**: Kafka integration even for 100 users
**Rationale**:
- Establishes scalable patterns early
- Enables audit trail and analytics
- Decouples components for independent scaling
- Natural progression to multi-cell architecture

### 4. JWT with Embedded Tier Information
**Decision**: Include subscription tier in JWT tokens
**Rationale**:
- Eliminates database lookups for authorization
- Enables edge-based rate limiting
- Supports stateless horizontal scaling
- Simplifies tier-based feature gating

### 5. Configuration-Driven Everything
**Decision**: Pydantic settings with environment variables
**Rationale**:
- 12-factor app compliance
- Type safety and validation
- Easy deployment across environments
- Self-documenting configuration

## Patterns Used

### 1. Repository Pattern (Storage)
```python
# Abstract interface
class StorageBackend(ABC):
    async def save(...)
    async def retrieve(...)
    async def delete(...)

# Concrete implementations
class MinIOBackend(StorageBackend):...
class AWSS3Backend(StorageBackend):...
```

### 2. Factory Pattern (Backend Creation)
```python
class BackendRegistry:
    @classmethod
    def create_backend(cls, config: BackendConfig) -> StorageBackend:
        # Dynamic loading based on type
```

### 3. Event Sourcing
- All state changes emit events
- Complete audit trail maintained
- Enables replay and debugging
- Foundation for CQRS if needed

### 4. Dependency Injection
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Routes use: db: AsyncSession = Depends(get_db)
```

### 5. Circuit Breaker (Planned)
- For external service calls (email, storage)
- Prevents cascading failures
- Graceful degradation

## Scaling Considerations

### Phase 1 → Phase 2 (100 → 1,000 users)
- **Database**: Connection pooling tuning
- **Events**: Increase Kafka partitions
- **Storage**: Enable CDN for presigned URLs
- **Auth**: Add Redis session caching

### Phase 2 → Phase 3 (1,000 → 10,000 users)
- **Database**: Read replicas for queries
- **Events**: Multi-broker Kafka cluster
- **Storage**: Multi-region replication
- **Auth**: Distributed rate limiting

### Phase 3 → Phase 4 (10,000 → 30,000+ users)
- **Database**: Sharding by user_id
- **Events**: Cross-region replication
- **Storage**: Global CDN with edge caching
- **Auth**: Edge-based JWT validation

### Current Optimizations
```python
# Connection pooling
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)

# Event batching ready
async def publish_events_batch(events: List[BaseEvent]):
    # Kafka supports batch publishing
```

## Security Considerations

### Authentication & Authorization
- **Bcrypt**: Secure password hashing with salt
- **JWT**: Short-lived tokens (7 days default)
- **Tier-based**: Access control via subscription tiers
- **User Isolation**: All queries filtered by user_id

### Data Protection
- **Encryption at Rest**: Backend-specific (S3 SSE, Azure encryption)
- **Encryption in Transit**: TLS for all external connections
- **Secrets Management**: Environment variables (move to Vault in Phase 2)
- **SQL Injection**: Parameterized queries via SQLAlchemy

### Storage Security
```python
# Automatic user namespacing
def generate_key(user_id: int, file_type: str, filename: str):
    return f"users/{user_id}/{file_type}/{timestamp}_{unique_id}_{filename}"

# Ownership verification
if not key.startswith(f"users/{user_id}/"):
    raise PermissionError("Access denied")
```

### Event Security
- **Partition by user_id**: Prevents cross-user data leakage
- **Event validation**: Pydantic models ensure data integrity
- **Access control**: Consumer groups for different services

## Technology Stack

### Core Technologies
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Async Framework** | asyncio + FastAPI | High performance, modern Python |
| **Database** | PostgreSQL + asyncpg | ACID compliance, JSON support, async |
| **ORM** | SQLAlchemy 2.0 | Async support, type safety |
| **Authentication** | JWT + bcrypt | Stateless, secure, industry standard |
| **Events** | Apache Kafka | Proven scale, ordering guarantees |
| **Storage** | Multi-backend | Flexibility, vendor independence |
| **Email** | SMTP + async | Simple, reliable, async sending |
| **Config** | Pydantic Settings | Type safety, validation |

### Storage Backends
- **Local**: Development and testing
- **MinIO**: Self-hosted S3 compatible
- **AWS S3**: Production scale, global reach
- **Azure Blob**: Enterprise integration

### Dependencies
```toml
# Core async stack
fastapi = "^0.104.1"
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
aiokafka = "^0.10.0"

# Storage backends (dynamically loaded)
aioboto3 = "^12.0.0"  # S3/MinIO
azure-storage-blob = "^12.19.0"  # Azure

# Security
python-jose = "^3.3.0"
bcrypt = "^4.1.2"
email-validator = "^2.1.0"
```

## Future Architecture Plans

### Phase 2 Enhancements
```
┌─────────────────────────────────┐
│      Go API Gateway             │
│   (Rate limiting, routing)      │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────┐
│         Core Services           │
│  + Redis Cache Layer            │
│  + Metrics Collection           │
│  + Circuit Breakers             │
└─────────────────────────────────┘
```

### Phase 3 Evolution
- **Database**: Vitess for sharding orchestration
- **Events**: Schema registry for evolution
- **Storage**: Intelligent tiering with ML
- **Auth**: OAuth2/OIDC provider support

### Phase 4 Global Scale
```
┌─────────────────────────────────────┐
│          Global Core Services        │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌─────────────────┐ │
│  │  CockroachDB │  │ Global Kafka  │ │
│  │  (Multi-region) │  │ MirrorMaker   │ │
│  └──────────┘  └─────────────────┘ │
│                                     │
│  ┌──────────┐  ┌─────────────────┐ │
│  │  Edge Auth  │  │ Global Storage │ │
│  │  (JWT@Edge) │  │   (Multi-CDN)  │ │
│  └──────────┘  └─────────────────┘ │
└─────────────────────────────────────┘
```

### Planned Improvements
1. **Observability**: OpenTelemetry integration
2. **Service Mesh**: Istio for internal communication
3. **Feature Flags**: Dynamic configuration
4. **A/B Testing**: Event-based experimentation
5. **Cost Optimization**: Usage tracking and limits

## Performance Considerations

### Current Optimizations
- **Connection Pooling**: Reuse database connections
- **Async I/O**: Non-blocking operations throughout
- **Event Batching**: Kafka producer batching
- **Lazy Loading**: Storage backends loaded on demand

### Monitoring Points
```python
# Key metrics to track
- Database pool utilization
- Event publishing latency
- Storage operation duration
- JWT validation time
- Email queue depth
```

### Bottleneck Mitigation
- **Database**: Prepared statements, indexing
- **Events**: Partition strategy, compression
- **Storage**: Presigned URLs bypass API
- **Email**: Queue with retry logic

## Conclusion

The Core service layer provides a solid foundation for the Resume Automation Platform, implementing enterprise-grade patterns while maintaining simplicity. Its event-driven architecture, multi-backend storage, and async-first design position it well for scaling from 100 to 30,000+ users without major architectural changes. The modular design allows for progressive enhancement as the platform grows, ensuring that complexity is added only when needed.
