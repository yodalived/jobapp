# Resume Personalization Engine - Technical Architecture

## Integration with Existing System

The Personalization Engine extends the current resume-automation platform, leveraging existing infrastructure:

- **Authentication**: Uses existing JWT/multi-tenant system
- **Database**: Extends current PostgreSQL schema
- **Events**: Integrates with existing Kafka infrastructure  
- **API**: New endpoints under `/api/v1/personalization/`
- **Frontend**: New pages in existing Next.js app
- **Dependencies**: Added to existing `pyproject.toml`

## Architecture Overview

### Data Flow Architecture

The personalization engine follows the established event-driven pattern:

1. Document Upload → SecurityFilterAgent → ClassificationAgent → ExtractionAgent
2. Extracted Facts → KnowledgeGraphService → VectorStore
3. Conversation → ConversationAgent → PatternExtractor → KnowledgeGraphService
4. Query → IntelligenceService → InsightGenerator → API Response

### Database Schema Extensions

New tables added to existing PostgreSQL database:

- `user_documents`: Uploaded document metadata
- `resume_items`: Structured career facts
- `knowledge_facts`: Verified and enriched facts
- `conversation_sessions`: Chat history and context
- `behavioral_patterns`: Extracted work patterns
- `skill_mappings`: O*NET skill relationships
- `career_insights`: Generated intelligence

### Event Schema Extensions

New Kafka events following existing patterns:

- `personalization.document.uploaded`
- `personalization.document.classified`
- `personalization.fact.extracted`
- `personalization.knowledge.updated`
- `personalization.insight.generated`
- `personalization.conversation.turn_completed`

## Component Architecture

### 1. Document Processing Pipeline

Located in: `src/personalization/services/document_processor/`

Components:
- `SecurityFilter`: MIME validation, content safety
- `DocumentClassifier`: Zero-shot classification
- `ContentExtractor`: Text extraction and parsing
- `FactExtractor`: Structured fact extraction
- `DeduplicationService`: Hash and semantic dedup

### 2. Knowledge Graph Service

Located in: `src/personalization/services/knowledge_graph/`

Components:
- `GraphManager`: Node and relationship management
- `FactRegistry`: Single source of truth for facts
- `ProvenanceTracker`: Audit trail for all facts
- `SkillOntology`: O*NET integration and mapping
- `RelationshipEngine`: Fact relationship discovery

### 3. Conversation Engine

Located in: `src/personalization/services/conversation_engine/`

Components:
- `ConversationOrchestrator`: Session management
- `AdaptiveQuestioner`: Dynamic question generation
- `GapAnalyzer`: Profile completeness analysis
- `BehavioralExtractor`: Pattern recognition
- `FatigueManager`: User engagement tracking

### 4. Intelligence Service

Located in: `src/personalization/services/intelligence/`

Components:
- `PatternRecognizer`: Career trajectory analysis
- `InsightGenerator`: Hidden strength discovery
- `CareerPathAnalyzer`: Alternative path finding
- `RecommendationEngine`: Personalized suggestions

## API Design

### New Router

`src/api/routers/personalization.py`

Endpoints:
- `POST /upload` - Document upload with streaming
- `GET /knowledge` - User knowledge dashboard data
- `PUT /knowledge/{fact_id}` - Fact editing
- `DELETE /knowledge/{fact_id}` - Fact deletion
- `POST /conversation/start` - Begin chat session
- `POST /conversation/turn` - Submit conversation turn
- `GET /insights` - Retrieved career insights
- `GET /skills/search` - O*NET skill search

### Request/Response Models

Located in: `src/api/models/personalization.py`

Using existing Pydantic patterns for validation and serialization.

## Security Architecture

### Multi-Tenant Isolation

- All queries include `user_id` filtering
- Vector namespaces isolated by user
- Row-level security on all tables
- No cross-tenant data leakage

### Content Security

- File upload limits: 10MB per file, 50MB total
- MIME whitelist: PDF, DOCX, TXT, PNG, JPG
- Content moderation via OpenAI API
- Quarantine system for rejected content

### Privacy Controls

- User-initiated data deletion
- Fact-level visibility controls
- Export functionality for GDPR
- Audit logs for all operations

## Performance Considerations

### Caching Strategy

- Redis cache for skill ontology (shared)
- User-specific fact cache (TTL: 1 hour)
- Embedding cache for deduplication
- Session state in Redis

### Async Processing

- Document processing via Kafka workers
- Embedding generation in background
- Batch operations for bulk updates
- Progress tracking via WebSocket

### Scalability

- Horizontal scaling via cell architecture
- Vector index partitioning by user
- Read replicas for analytics
- Event stream partitioning

## Integration Points

### With Existing Resume Generator

- Knowledge graph provides verified facts
- Tone analyzer provides writing style
- Skill mapping enhances keyword optimization
- Behavioral patterns inform soft skills

### With Existing Job Matching

- Enhanced skill matching via ontology
- Better cultural fit assessment
- More accurate role recommendations
- Transferable skill identification

## Development Setup

### Dependencies to Add

Update `pyproject.toml`:

[tool.poetry.dependencies]
# Document processing
python-docx = "^0.8.11"
pdfplumber = "^0.9.0"
pypdf2 = "^3.0.1"

# NLP and ML
spacy = "^3.7.0"
sentence-transformers = "^2.2.2"
scikit-learn = "^1.3.0"

# Vector storage
pgvector = "^0.2.0"

# Conversation
langchain = "^0.1.0"

# Graph operations
networkx = "^3.1"

### Environment Variables

Add to `.env`:

# Personalization settings
PERSONALIZATION_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PERSONALIZATION_CHUNK_SIZE=512
PERSONALIZATION_CHUNK_OVERLAP=50
ONET_API_KEY=your_key_here
CONTENT_MODERATION_THRESHOLD=0.7

### Database Migrations

New Alembic migration: `alembic/versions/xxx_add_personalization_tables.py`

## Testing Strategy

### Unit Tests

- `tests/personalization/test_extractors.py`
- `tests/personalization/test_deduplication.py`
- `tests/personalization/test_skill_mapping.py`

### Integration Tests

- `tests/personalization/test_document_pipeline.py`
- `tests/personalization/test_conversation_flow.py`
- `tests/personalization/test_insight_generation.py`

### Performance Tests

- Document processing throughput
- Vector search latency
- Conversation response time
- Bulk operation performance

## Monitoring

### Metrics to Track

- Documents processed per minute
- Facts extracted per document
- Conversation completion rate
- Insight generation accuracy
- User engagement metrics

### Alerts

- Failed document processing
- High deduplication rate (>50%)
- Low conversation engagement
- Vector search latency >200ms

## Deployment Considerations

### Resource Requirements

- Additional PostgreSQL storage: ~100GB
- Redis memory increase: ~2GB
- CPU for ML models: 2-4 cores
- GPU optional for embeddings

### Migration Plan

1. Deploy schema migrations
2. Load O*NET data
3. Enable document upload
4. Roll out conversation engine
5. Activate intelligence features

### Rollback Strategy

- Feature flags for each component
- Separate Kafka topics for isolation
- Database migrations reversible
- No changes to existing features
