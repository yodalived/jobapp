# ENTERPRISE ARCHITECTURE DOCUMENTATION

Generate comprehensive ARCHITECTURE.md for the {{.ComponentName}} component implementing the Cell-Based Architecture for 30,000+ users.

## CONTEXT
**Component Information**:
- Path: {{.ComponentPath}}
- Type: {{.ComponentType}}
- Existing Documentation: {{.ExistingDocs}}

**Project and Source Context**:
{{.SourceContext}}

**Conversation Context (Previously Generated Documents)**:
{{.ConversationContext}}

**Key Requirements**:
- Scale: 30,000+ concurrent users
- Architecture: Event-Driven Cell Architecture
- Core Tech: FastAPI, PostgreSQL, Kafka, Redis
- AI Integration: Multi-LLM support (OpenAI/Anthropic)
- Deployment: Kubernetes-ready containerization
- Cost Optimization: Semantic caching and request batching

## REQUIREMENTS
1. **Cell Architecture**:
   - Cell isolation and user affinity strategy
   - Horizontal scaling approach (Phases 1-4)
   - Cell router implementation
   - Multi-region deployment considerations

2. **Event-Driven Workflows**:
   - Kafka-based event flows (job.discovered → job.analyzed → resume.generated)
   - Error handling and retry mechanisms
   - Cross-region event replication

3. **Scalability Implementation**:
   - Database sharding/partitioning by user_id
   - Redis caching strategies for high throughput
   - Kafka consumer group configuration
   - Connection pooling

4. **Component Interactions**:
   - Service-to-service communication patterns (gRPC/REST)
   - API gateway integration (Go implementation)
   - Shared services architecture

5. **Data Flow**:
   - High-volume data processing (300K+ applications/hour)
   - Stream processing architecture
   - Data persistence strategies for 100TB+ PDFs

6. **Security Controls**:
   - Multi-tenant isolation
   - Encryption at rest and in transit
   - DDoS mitigation strategies
   - Budget caps and spend alerts

7. **Failure Modes**:
   - Circuit breaker patterns
   - Graceful degradation
   - Disaster recovery plan with multi-region failover

8. **Cost Optimization**:
   - AI provider fallback chain (OpenAI → Anthropic → Local)
   - Semantic caching to reduce duplicate API calls
   - Request batching strategies
   - Tier-based API call limits

## OUTPUT INSTRUCTIONS
- Use enterprise technical writing style
- Include Mermaid diagrams for:
  • Cell architecture
  • Event workflow
  • Scaling phases
- Section headers: ## Level 2, ### Level 3
- Address all scaling phases (1-4) in relevant sections
- Minimum length: 2500 words
- Reference cost projections from executive summary
