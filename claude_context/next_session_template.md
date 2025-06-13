# Next Session Template

I'm continuing work on my resume automation system. Current status:

## Completed
- Multi-tenant architecture with user authentication
- JWT-based auth with subscription tiers
- All endpoints protected and user-scoped
- Database models with user relationships
- Full CRUD API for job applications

## Project Structure
- FastAPI with PostgreSQL/Redis
- Authentication with JWT tokens
- Multi-tenant (each user sees only their data)
- Subscription tiers: FREE, STARTER, PROFESSIONAL, ENTERPRISE

## Current Task
[SPECIFY: email verification, resume generator, linkedin scraper, etc.]

## Key Files
- src/api/routers/applications.py - Protected CRUD endpoints
- src/api/routers/auth.py - Auth endpoints
- src/api/models/auth.py - User model with SaaS features
- src/api/dependencies.py - get_current_user dependency

## To Start Development
source venv/bin/activate
docker-compose up -d postgres redis
poetry run uvicorn src.api.main:app --reload

## Auth Testing
# Get token
curl -X POST http://localhost:8000/api/v1/auth/login -d "username=test@example.com&password=password123"
# Use token
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/applications/

[PASTE SPECIFIC QUESTION/ERROR]
