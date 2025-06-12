# claude_context/quick_reference.md

## Database Connection Test
```python
# Test database connection
from src.core.database import engine, AsyncSessionLocal
from src.api.models.schema import JobApplication

# Async test
async def test_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute("SELECT 1")
        print(result.scalar())

Common Imports
# FastAPI
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.core.database import get_db

# Models
from src.api.models.schema import JobApplication, Company, ResumeVersion
from src.api.models.schemas import JobApplicationCreate, JobApplicationResponse
Environment Variables Required
DATABASE_URL
ASYNC_DATABASE_URL
REDIS_URL
SECRET_KEY

# Docker Commands
docker start resume-postgres resume-redis
docker stop resume-postgres resume-redis
docker ps  # Check running

# Current Enum Values
ApplicationStatus: discovered, queued, applied, acknowledged, screening, interview, offer, rejected, withdrawn
JobType: technical, management, hybrid

## Commit These Updates

```bash
# Stage all documentation updates
git add PROJECT_STATUS.md
git add claude_context/current_code_structure.md
git add claude_context/next_session_template.md
git add claude_context/quick_reference.md

# Commit with clear message
git commit -m "docs: Update documentation after successful database setup

- Database models created and migrated
- Alembic configured and working
- Updated all context files for next session
- Added quick reference guide
- Note: metadata columns renamed to extra_data"

# Check your work
git log --oneline -5
