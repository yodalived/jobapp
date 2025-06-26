# Architecture Decisions

Document key design choices and their reasoning for future context.

## Database Architecture

### Decision: Multi-Tenant PostgreSQL with User Isolation
**Date**: 2024-06-13  
**Context**: Building SaaS platform requiring data isolation between users
**Options Considered**:
1. Separate databases per tenant
2. Schema-per-tenant  
3. Row-level security with user_id filtering
**Decision**: Row-level security with user_id filtering
**Reasoning**:
- Simpler deployment and maintenance
- Cost-effective for small-medium scale
- Easy to implement with SQLAlchemy
- Can migrate to schema-per-tenant later if needed
**Implementation**: All models include `user_id` field, queries filtered automatically
**Trade-offs**: Less isolation than separate schemas, but much simpler

### Decision: Async SQLAlchemy with asyncpg
**Date**: 2024-06-13
**Context**: Need high-performance database operations for API
**Decision**: Use async SQLAlchemy with asyncpg driver
**Reasoning**:
- Better performance for I/O-bound operations
- Modern Python async patterns
- FastAPI async compatibility
- Scales better under load
**Implementation**: All database operations use `async def` and `await`
**Trade-offs**: Slightly more complex than sync, but performance benefits worth it

## Authentication & Authorization

### Decision: JWT with Subscription Tiers
**Date**: 2024-06-13
**Context**: SaaS platform needs user auth and feature gating
**Decision**: JWT tokens with embedded tier information
**Reasoning**:
- Stateless authentication scales well
- Tier information in token enables fast authorization checks
- Standard approach with good library support
**Implementation**: 
- JWT contains user_id, tier, and expiration
- Dependency injection for current_user in routes
- Tier-based limits enforced at API level
**Trade-offs**: Token size larger with tier info, but avoids database lookups

## Resume Generation

### Decision: LaTeX + Jinja2 Templates
**Date**: 2024-06-13
**Context**: Need professional PDF output with flexible templating
**Options Considered**:
1. HTML + CSS to PDF (wkhtmltopdf, Puppeteer)
2. LaTeX templating
3. Native PDF libraries (ReportLab)
**Decision**: LaTeX with Jinja2 templating
**Reasoning**:
- Superior typography and professional appearance
- Flexible templating with Jinja2
- Industry standard for academic/professional documents
- Better control over layout and formatting
**Implementation**: Jinja2 renders LaTeX, pdflatex compiles to PDF
**Trade-offs**: Requires pdflatex installation, but output quality superior

### Decision: Selective LaTeX Escaping
**Date**: 2024-06-14
**Context**: AI-generated content contains special characters that break LaTeX
**Options Considered**:
1. Escape all content globally
2. Escape only dynamic template variables
3. Pre-process AI content before template rendering
**Decision**: Escape only dynamic template variables using Jinja2 filters
**Reasoning**:
- Preserves LaTeX template structure
- Minimal performance impact
- Clear separation between template and content
- Easy to apply selectively where needed
**Implementation**: `{{ variable|latex_escape }}` in templates
**Trade-offs**: Must remember to apply filter, but gives precise control

## LLM Integration

### Decision: Multi-Provider Architecture with Fallback
**Date**: 2024-06-13
**Context**: Want flexibility in LLM providers and resilience to API issues
**Decision**: Provider-agnostic service with OpenAI and Anthropic support
**Reasoning**:
- Vendor independence and cost optimization
- Different models for different use cases
- Resilience to API outages or rate limits
- Easy to add new providers
**Implementation**: 
- Abstract `LLMProvider` base class
- `LLMService` handles provider selection and fallback
- Configuration-driven provider choice
**Trade-offs**: More complex than single provider, but much more flexible

### Decision: Structured Prompts with JSON Output
**Date**: 2024-06-13
**Context**: Need reliable, parseable output from LLMs
**Decision**: Use structured prompts requesting JSON responses
**Reasoning**:
- More reliable than free-form text parsing
- Enables validation and error handling
- Consistent output format across providers
- Easier to integrate with application logic
**Implementation**: Prompts specify exact JSON schema, parse and validate responses
**Trade-offs**: Slightly more rigid, but much more reliable

## File Management

### Decision: Local File Storage with Organized Directory Structure
**Date**: 2024-06-13
**Context**: Need to store generated PDFs and LaTeX source
**Options Considered**:
1. Database storage (BLOBs)
2. Cloud storage (S3, etc.)
3. Local filesystem
**Decision**: Local filesystem with organized directory structure
**Reasoning**:
- Simple deployment and development
- Fast access for generated files
- Easy debugging and file inspection
- Can migrate to cloud storage later
**Implementation**: `resume_outputs/` directory with organized naming
**Trade-offs**: Not scalable across multiple servers, but simple for current needs

### Decision: Cross-Platform File Operations
**Date**: 2024-06-14
**Context**: File operations failing across different filesystems
**Decision**: Use `shutil.move()` instead of `Path.rename()`
**Reasoning**:
- Works across device boundaries
- More robust error handling
- Standard library solution
- Platform-independent
**Implementation**: Replace all `rename()` calls with `shutil.move()`
**Trade-offs**: Slightly slower for same-device moves, but much more reliable

## API Design

### Decision: FastAPI with Async Patterns
**Date**: 2024-06-13
**Context**: Need modern, fast API framework with good documentation
**Decision**: FastAPI with full async support
**Reasoning**:
- Excellent performance for I/O-bound operations
- Automatic OpenAPI documentation generation
- Strong typing with Pydantic
- Modern Python async patterns
- Great developer experience
**Implementation**: All routes use `async def`, Pydantic models for validation
**Trade-offs**: Learning curve for async patterns, but performance and DX benefits huge

### Decision: Router-Based Organization
**Date**: 2024-06-13
**Context**: Need organized API structure as system grows
**Decision**: Separate routers for logical groupings (auth, applications, generator)
**Reasoning**:
- Clear separation of concerns
- Easier to maintain and test
- Better code organization
- Enables team development
**Implementation**: `routers/` directory with logical groupings
**Trade-offs**: More files to manage, but much better organization

## Testing Strategy

### Decision: Integration Tests Over Unit Tests
**Date**: 2024-06-14
**Context**: Complex system with many moving parts (API, DB, LLMs, LaTeX)
**Decision**: Focus on integration tests that verify full workflows
**Reasoning**:
- Catches real-world interaction issues
- Validates complete user workflows
- Easier to maintain than extensive mocking
- Provides confidence in deployments
**Implementation**: Test scripts that exercise full system capabilities
**Trade-offs**: Slower test execution, but higher confidence in system behavior

---

## Decision Review Schedule

### Quarterly Reviews
- Multi-tenant approach: Is row-level security still sufficient?
- File storage: Time to move to cloud storage?
- LLM providers: Are we using the best available models?

### Triggered Reviews
- **Performance Issues**: Consider caching, database optimizations
- **Scale Issues**: Consider microservices, separate databases
- **Security Concerns**: Review auth patterns, data isolation
- **Cost Issues**: Review provider choices, optimization opportunities

---

## Template for New Decisions

```markdown
### Decision: [Title]
**Date**: YYYY-MM-DD
**Context**: [Why this decision was needed]
**Options Considered**:
1. [Option 1 with pros/cons]
2. [Option 2 with pros/cons]
**Decision**: [What was chosen]
**Reasoning**:
- [Key reason 1]
- [Key reason 2]
**Implementation**: [How it was implemented]
**Trade-offs**: [What we gave up and what we gained]
**Review Date**: [When to reconsider this decision]
```