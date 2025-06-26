# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Resume Automation Platform - A multi-tenant SaaS platform designed to scale from 100 to 30,000+ users. Built with event-driven architecture using FastAPI, PostgreSQL, Kafka, and Next.js. Currently in Phase 1 Complete with 94% feature completion.

## Current Status
- ✅ **Phase 1 Architecture**: Complete event-driven system with Kafka + Agents + Workflows
- ✅ **Frontend Integration**: Next.js application with full authentication flow
- ✅ **AI Integration**: Multi-LLM support (OpenAI/Anthropic) with job analysis
- ✅ **Resume Generation**: LaTeX templates with PDF compilation
- ✅ **Authentication**: Complete with JWT, email verification, SMTP integration
- ✅ **Testing**: Comprehensive integration test suite + development tools
- 🚧 **Phase 1**: 94% complete (32/34 features) - only Dashboard UI remaining
- 🚧 **Ready for Phase 2**: Go gateway, worker separation, enhanced monitoring

## Development Memories
- Always end files with a carriage return
- Do not mention claude in any git commit
- This is an enterprise application. Design accordingly.
- Use event-driven patterns throughout (Kafka producers/consumers)
- Maintain cell architecture for future scaling
- Always remember to source ~/src/resume-automation/venv/bin/activate when running any python commands or sub commands or python related commands.
- We are using poetry to install python modules. Do not us pip unless absolutely necessary.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Configure poetry to use local venv
poetry env use venv/bin/python

# Install dependencies
poetry install

# Start services (PostgreSQL, Redis, Kafka, Zookeeper)
docker-compose up -d postgres redis zookeeper kafka

# Run database migrations
poetry run alembic upgrade head

# Start API server (backend)
poetry run uvicorn src.api.main:app --reload
# OR use the convenience script:
./start_api.sh

# Start frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

### Testing Commands
```bash
# Run comprehensive integration tests
python test-scripts/test_all_endpoints.py

# Test resume generation with AI and PDF
python test-scripts/test_resume_generation.py

# Test LaTeX escaping
python test-scripts/test_latex_escaping.py

# Test Kafka events
python test_resume_and_events.py

# Code quality checks
poetry run ruff check .
```

### Access Points
- **Frontend**: http://localhost:3080 (Main SaaS application)
- **API Documentation**: http://localhost:8048/docs (FastAPI interactive docs)
- **Status Dashboard**: http://localhost:3080/status (Interactive roadmap with expandable details)
- **Kafka UI**: http://localhost:9080 (Event stream monitoring)
- **Health Check**: http://localhost:8048/health (Service status)

## Storage Backend Configuration

### 🔄 **Switch Storage Backends** (Zero Code Changes)

The platform supports multiple storage backends that can be switched instantly via `.env` configuration:

#### Available Backends:
- **Local** (`local`): File system storage for development
- **MinIO** (`minio`): S3-compatible object storage for staging/production  
- **AWS S3** (`aws_s3`): Native AWS S3 with Glacier, encryption, intelligent tiering
- **Azure Blob** (`azure_blob`): Azure Blob Storage with Hot/Cool/Archive tiers

#### Switch to MinIO (Your Setup):
```bash
# .env file
PRIMARY_BACKEND=minio
MINIO_ENDPOINT_URL=http://your-minio-server:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=your-bucket-name
MINIO_SECURE=false
```

#### Switch to Local Development:
```bash
# .env file
PRIMARY_BACKEND=local
LOCAL_STORAGE_PATH=./storage
```

#### Check Backend Status:
```python
# In Python shell or script
from src.core.storage.manager import StorageManager, BackendRegistry

# List available backends
print("Available:", BackendRegistry.list_available_backends())

# Check backend info
for backend in BackendRegistry.list_all_backends():
    info = BackendRegistry.get_backend_info(backend)
    print(f"{backend}: {info['status']}")
```

## Important Notes
- **Database Migrations**: The latest migration file has reversed up/down functions - see HANDOFF.md
- **Email Service**: Configure SMTP in .env or system will gracefully use console logging
- **Test User**: Use yodalives@gmail.com for testing - deletable via status page button
- **Poetry**: Always use Poetry for Python packages, not pip
- **Storage**: All storage backends are pre-installed and switch via configuration only

## Authentication Flow
### Registration Process
- Registration endpoint (`/auth/register`) creates user account but does NOT return auth token
- Frontend automatically calls login endpoint after successful registration
- This provides seamless user experience without manual login step
- Users are redirected to dashboard with proper authentication

### Email Verification UX
- Unverified users can access dashboard but see persistent verification banner
- Banner explains feature limitations (2 resume limit, no job applications)
- Banner cannot be dismissed until email is verified

### GitHub-Style Navigation (Latest Update)
- **Homepage accessible to all**: Logged-in users can browse marketing site
- **Smart redirects**: Only auth pages (login/register) redirect to dashboard
- **Professional top navigation**: Shows user stats (resumes, applications) and welcome message
- **User dropdown menu**: Industry-standard profile dropdown with logout functionality
- **Seamless UX**: Users can explore marketing content while having workspace access

### Frontend Authentication State
- Homepage detects authentication and shows personalized navigation
- Marketing content remains identical for logged-in and logged-out users
- Stats displayed in professional pills in top navigation bar
- Full logout functionality with proper state clearing