# Quick Reference Guide

## Common Commands
# Start development
source venv/bin/activate
docker-compose up -d postgres redis
poetry run uvicorn src.api.main:app --reload

# Run migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Test endpoints
export TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/applications/

## Project Structure
src/
├── api/
│   ├── models/          # SQLAlchemy models
│   ├── routers/         # API endpoints
│   └── dependencies.py  # Auth dependencies
├── core/               # Config, database
├── generator/          # Resume generation
│   ├── templates/      # LaTeX templates
│   ├── llm_interface.py
│   └── resume_customizer_rag.py
└── worker/            # Celery tasks (future)

## Key Imports
from src.api.dependencies import get_current_active_user
from src.core.database import get_db
from src.generator.resume_generator import ResumeGenerator
from src.generator.resume_customizer_rag import ResumeCustomizerWithRAG

## Environment Variables
DATABASE_URL=postgresql://...
ASYNC_DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

## Testing Flow
1. Register user
2. Login to get token
3. Create job application
4. Generate customized resume
5. Check PDF output

## Common Issues
- LaTeX not installed: sudo apt-get install texlive-latex-base texlive-fonts-extra
- Import errors: Check PYTHONPATH or use poetry run
- Auth errors: Token expired or missing Bearer prefix
- PDF generation fails: Check LaTeX syntax and escaping
