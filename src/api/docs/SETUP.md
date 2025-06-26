# SETUP.md - API Component

This guide will help you set up the API component of the Resume Automation Platform. The API serves as the primary interface layer, providing authentication, job application management, resume generation, and file handling capabilities.

## 📋 Prerequisites

### Required Software
- **Python 3.11+** - Core runtime environment
- **Poetry** - Python dependency management and packaging
- **Docker & Docker Compose** - For running external services
- **PostgreSQL 13+** - Primary database (via Docker)
- **Redis 6+** - Caching and session storage (via Docker)
- **Apache Kafka 2.8+** - Event streaming platform (via Docker)
- **pdflatex** - LaTeX distribution for PDF generation

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for Docker images and dependencies
- **Network**: Internet access for downloading dependencies and AI API calls

### Check Prerequisites
```bash
# Check Python version
python --version  # Should be 3.11+

# Check Poetry installation
poetry --version  # If not installed: pip install poetry

# Check Docker
docker --version && docker-compose --version

# Check pdflatex (for resume generation)
pdflatex --version  # If missing: sudo apt-get install texlive-latex-base (Ubuntu/Debian)
```

## 🚀 Installation Steps

### 1. Clone Repository and Navigate to Project
```bash
git clone <repository-url>
cd resume-automation
```

### 2. Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Configure Poetry to use the virtual environment
poetry env use venv/bin/python
```

### 3. Install Python Dependencies
```bash
# Install all dependencies via Poetry
poetry install

# Verify installation
poetry show  # Lists all installed packages
```

**Expected output should include:**
- fastapi>=0.104.0
- sqlalchemy>=2.0.0
- asyncpg>=0.29.0
- aiokafka>=0.8.0
- openai>=1.3.0
- anthropic>=0.7.0

### 4. Start External Services
```bash
# Start PostgreSQL, Redis, Kafka, and Zookeeper
docker-compose up -d postgres redis zookeeper kafka

# Verify services are running
docker-compose ps
```

**Expected output:**
```
NAME                    COMMAND                  SERVICE             STATUS              PORTS
resume_postgres         "docker-entrypoint.s…"   postgres            running             0.0.0.0:5432->5432/tcp
resume_redis            "docker-entrypoint.s…"   redis               running             0.0.0.0:6379->6379/tcp
resume_kafka            "/etc/confluent/dock…"   kafka               running             0.0.0.0:9092->9092/tcp
resume_zookeeper        "/etc/confluent/dock…"   zookeeper           running             2181/tcp, 2888/tcp, 3888/tcp
```

### 5. Database Setup
```bash
# Run database migrations
poetry run alembic upgrade head
```

**Note**: If migrations fail, you may need to create tables manually. Check the troubleshooting section.

## ⚙️ Configuration Requirements

### 1. Environment Variables File
```bash
# Copy example environment file
cp .env.example .env

# Edit the file with your specific settings
nano .env  # or your preferred editor
```

### 2. Required Configuration Files
- **`.env`** - Environment variables (copy from .env.example)
- **`alembic.ini`** - Database migration settings (pre-configured)
- **`pyproject.toml`** - Python dependencies (pre-configured)

## 🔧 Environment Variables

### Essential Variables
```bash
# Core Settings
PROJECT_NAME="Resume Automation Platform"
SECRET_KEY=your-super-secret-key-here  # Generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_PREFIX=/api/v1

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_automation
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_automation

# Cache & Sessions
REDIS_URL=redis://localhost:6379

# Event Streaming
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### AI Provider Configuration (At least one required)
```bash
# OpenAI Integration
OPENAI_API_KEY=sk-your-openai-key-here
DEFAULT_LLM_PROVIDER=openai

# Anthropic Integration (optional)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# LLM Settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### Email Service Configuration (Optional)
```bash
# SMTP Configuration (graceful fallback if not configured)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app-specific password for Gmail
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="ResumeAI Platform"
```

### Security & CORS
```bash
# CORS Configuration (adjust for your frontend)
ALLOWED_ORIGINS=["http://localhost:3080", "http://localhost:8000"]

# File Upload Limits
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=[".pdf", ".doc", ".docx", ".txt"]
```

### Generate Secure Secret Key
```bash
# Generate a secure secret key
openssl rand -hex 32
# Copy the output to SECRET_KEY in your .env file
```

## 🗄️ Database/Service Setup

### PostgreSQL Database
```bash
# Connect to database (for verification)
docker exec -it resume_postgres psql -U postgres -d resume_automation

# Inside PostgreSQL, check tables:
\dt
# Should show: users, job_applications, companies, resume_versions, etc.

# Exit PostgreSQL
\q
```

### Redis Cache
```bash
# Test Redis connection
docker exec -it resume_redis redis-cli ping
# Expected response: PONG
```

### Kafka Event Streaming
```bash
# List Kafka topics (should be empty initially)
docker exec -it resume_kafka kafka-topics --bootstrap-server localhost:9092 --list

# Access Kafka UI (optional but helpful)
# Open: http://localhost:9080
```

### Create Database Tables (If Migration Fails)
```sql
-- If alembic migrations fail, manually create essential tables:
docker exec -it resume_postgres psql -U postgres -d resume_automation

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR,
    subscription_tier VARCHAR DEFAULT 'free',
    applications_count INTEGER DEFAULT 0,
    resumes_generated_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## ✅ Verification Steps

### 1. Start the API Server
```bash
# Method 1: Using Poetry
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8048

# Method 2: Using start script (if available)
./start_api.sh
```

**Expected output:**
```
🚀 Starting Resume Automation Platform...
✅ Database connection successful
✅ Redis connection successful
✅ Kafka connection successful

✅ API ready at http://localhost:8048
📚 Documentation at http://localhost:8048/docs
🎛️ Kafka UI at http://localhost:9080
```

### 2. Test API Endpoints
```bash
# Test root endpoint
curl http://localhost:8048/
# Expected: {"message": "Resume Automation Platform", "version": "0.1.0"}

# Test health check
curl http://localhost:8048/health
# Expected: {"status": "healthy", "services": {"database": "healthy", ...}}
```

### 3. Access API Documentation
Open your browser and navigate to:
- **API Docs**: http://localhost:8048/docs
- **Alternative Docs**: http://localhost:8048/redoc

### 4. Run Integration Tests
```bash
# Run comprehensive test suite
python test-scripts/test_all_endpoints.py

# Expected output:
# ✅ Root endpoint working
# ✅ Health check working
# ✅ Auth endpoints working
# ✅ All tests passed!
```

### 5. Test Resume Generation
```bash
# Test full resume generation pipeline
python test-scripts/test_resume_generation.py

# Expected output:
# ✅ Output Directory Test
# ✅ Template Availability Test  
# ✅ Basic Generation Test
# ✅ AI Customization Test
# 🎉 All tests passed!
```

## 🔧 Development Environment Setup

### 1. Development Tools
```bash
# Install development dependencies (included in poetry install)
poetry install --with dev

# Set up pre-commit hooks (optional)
pre-commit install
```

### 2. Code Quality Tools
```bash
# Run linting
poetry run ruff check .

# Format code
poetry run ruff format .

# Type checking (if mypy is installed)
poetry run mypy src/
```

### 3. Development Server with Auto-reload
```bash
# Start with auto-reload for development
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8048

# Or use the development start script
./start_api.sh
```

### 4. Database Development
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Downgrade migrations (if needed)
poetry run alembic downgrade -1
```

## 🚨 Troubleshooting Common Issues

### Issue: Database Connection Failed
**Symptoms**: `Database connection failed` on startup

**Solutions**:
```bash
# 1. Check if PostgreSQL is running
docker-compose ps | grep postgres

# 2. Start PostgreSQL if not running
docker-compose up -d postgres

# 3. Check database URL in .env
echo $DATABASE_URL

# 4. Verify database exists
docker exec -it resume_postgres psql -U postgres -l
```

### Issue: Migration Errors
**Symptoms**: `alembic upgrade head` fails

**Solutions**:
```bash
# 1. Check current migration status
poetry run alembic current

# 2. Check migration history
poetry run alembic history

# 3. If migrations are broken, create tables manually (see Database Setup section)

# 4. Reset migrations (DESTRUCTIVE - only for development)
docker exec -it resume_postgres psql -U postgres -c "DROP DATABASE resume_automation;"
docker exec -it resume_postgres psql -U postgres -c "CREATE DATABASE resume_automation;"
poetry run alembic upgrade head
```

### Issue: pdflatex Not Found
**Symptoms**: Resume generation fails with LaTeX errors

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-fonts-recommended

# macOS
brew install --cask mactex-no-gui

# Windows
# Download and install MiKTeX from https://miktex.org/

# Test installation
pdflatex --version
```

### Issue: AI API Integration Fails
**Symptoms**: LLM provider errors or "API key not configured"

**Solutions**:
```bash
# 1. Check API keys are set
echo $OPENAI_API_KEY | cut -c1-10
echo $ANTHROPIC_API_KEY | cut -c1-10

# 2. Test API keys manually
python -c "
import openai
client = open