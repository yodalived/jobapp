# Current State of Resume Automation Project

## What's Working
- Complete multi-tenant job application tracking
- JWT authentication with subscription tiers
- Resume generation with LaTeX templates
- AI customization with OpenAI and Claude
- Industry-specific prompts and RAG documents
- Multiple LLM provider support

## Architecture Overview
User → FastAPI → LLM (OpenAI/Claude) → LaTeX → PDF
               ↓
        PostgreSQL (data)
        Redis (cache/queues)

## Latest Features
1. **Industry-Specific Customization**
  - System prompts for different industries (tech, finance, marketing)
  - RAG documents with best practices
  - Industry templates with tips

2. **Multi-LLM Support**
  - OpenAI (GPT-4/GPT-3.5)
  - Anthropic (Claude)
  - Automatic fallback
  - Provider comparison

3. **RAG System**
  - Store resume guidelines
  - Industry-specific examples
  - ATS optimization rules
  - Custom user documents

## Database Schema Updates
New tables added:
- system_prompts (AI prompts by industry)
- rag_documents (guidelines and examples)
- industry_templates (industry configs)

## API Structure
/api/v1/
├── auth/          # Login, register, user info
├── applications/  # Job application CRUD
├── generator/     # Resume generation
└── customization/ # Prompts and RAG management

## Resume Generation Flow
1. User creates job application with description
2. System analyzes job (extract skills, level, keywords)
3. User selects industry/prompt or uses auto-detect
4. RAG documents provide context
5. LLM customizes resume content
6. LaTeX generates professional PDF
7. PDF linked to application

## Testing Flow
# 1. Register/Login
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123"}'
curl -X POST http://localhost:8000/api/v1/auth/login -d "username=test@example.com&password=password123"

# 2. Create application  
export TOKEN="your-jwt-token"
curl -X POST http://localhost:8000/api/v1/applications/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"company": "Tech Corp", "position": "Senior Engineer", "url": "https://example.com/job/123", "job_description": "Looking for senior engineer..."}'

# 3. Generate resume
curl -X POST http://localhost:8000/api/v1/generator/generate-with-rag -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"application_id": 1, "master_resume_data": {...}, "industry": "tech", "customize_with_ai": true}'
