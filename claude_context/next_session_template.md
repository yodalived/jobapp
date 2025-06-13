# Resume Automation Project - Session Start Template

## Project Overview
Multi-tenant SaaS for automated resume generation and job tracking with AI customization.

## Current Status
- ✅ Complete authentication system with JWT
- ✅ Job application tracking API
- ✅ Resume generation with LaTeX
- ✅ Multi-LLM support (OpenAI + Claude)
- ✅ Industry-specific prompts and RAG
- ⏳ Need: LinkedIn scraper, Frontend, Email verification

## Tech Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis
- Auth: JWT with subscription tiers
- AI: OpenAI/Claude with RAG
- Resume: LaTeX → PDF
- Queue: Celery (configured but not implemented)

## Quick Start
source venv/bin/activate
docker-compose up -d postgres redis
poetry run uvicorn src.api.main:app --reload

## Recent Additions
1. Industry-specific system prompts
2. RAG document storage
3. Multi-LLM provider support
4. Enhanced resume customization

## Database Tables
Core: users, job_applications, resume_versions, companies
New: system_prompts, rag_documents, industry_templates

## Key Endpoints
- POST /api/v1/generator/generate-with-rag - AI resume generation
- GET /api/v1/customization/prompts - List prompts
- POST /api/v1/customization/rag-documents - Add guidelines

## Environment Setup
Required in .env:
- DATABASE_URL, ASYNC_DATABASE_URL
- REDIS_URL, SECRET_KEY
- OPENAI_API_KEY and/or ANTHROPIC_API_KEY

## Next Priority
[SPECIFY: LinkedIn scraper, Frontend, Embeddings, etc.]

## Current Task
[PASTE SPECIFIC QUESTION/TASK]
