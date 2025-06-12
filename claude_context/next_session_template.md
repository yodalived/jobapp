# Template for Starting Next Claude Session

## Opening Message Template

I'm continuing work on my resume automation system in Python. Here's the current status:

**Project**: Automated resume generation and job application tracking system

**Completed So Far**:
- Project structure with Poetry
- PostgreSQL & Redis running in Docker
- Database models (JobApplication, Company, ResumeVersion, etc.)
- Alembic migrations configured and run
- Tables successfully created in database

**Current Database Schema**:
- job_applications (main tracking)
- application_status_history
- application_notes
- companies
- resume_versions

**Next Task**: Create FastAPI endpoints for CRUD operations on job applications

**Tech Stack**:
- FastAPI (async API)
- PostgreSQL + SQLAlchemy + Alembic
- Redis + Celery
- Playwright (scraping)
- LangChain + OpenAI

**Current Working Directory Structure**:
src/
├── api/
│   ├── models/
│   │   ├── schema.py   # SQLAlchemy models
│   │   └── schemas.py  # Pydantic models
│   └── main.py        # Need to create this
├── core/
│   ├── config.py      # Settings
│   └── database.py    # DB connection

**Specific Question**: [FILL IN]

[PASTE ANY RELEVANT CODE OR ERRORS]

## Key Context Points
- Using Python-only (no Go)
- Have existing K8s cluster for eventual deployment
- Starting with LinkedIn Easy Apply
- Changed all 'metadata' columns to 'extra_data' in models
- Both asyncpg and psycopg2-binary installed
