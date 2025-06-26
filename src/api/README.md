# API Component

The API component serves as the primary interface layer for the Resume Automation Platform, providing a comprehensive RESTful API built with FastAPI. It handles authentication, job application management, resume generation orchestration, and file operations while maintaining strict multi-tenant isolation and preparing for horizontal scaling to 30,000+ users.

## 🎯 Component Overview

The API component is the central nervous system of the platform, orchestrating all user interactions and business logic. It implements a modern async-first architecture with event-driven patterns, supporting the platform's journey from 100 users in Phase 1 to 30,000+ users in Phase 4.

### Core Responsibilities
- **Authentication & Authorization**: JWT-based multi-tenant security with subscription tiers
- **Job Application Management**: Complete CRUD operations with status tracking
- **Resume Generation**: AI-powered resume creation and customization
- **File Operations**: Secure file upload, storage, and retrieval
- **Event Orchestration**: Kafka integration for asynchronous workflows
- **Multi-Tenant Isolation**: Row-level security ensuring data separation

## 🚀 Key Features

### Authentication System
- **JWT Authentication**: Stateless tokens with subscription tier information
- **Email Verification**: Required verification flow with SMTP integration
- **Multi-Tenant Security**: User-scoped data access with automatic filtering
- **Subscription Tiers**: Free, Starter, Professional, Enterprise with usage limits
- **Password Security**: bcrypt hashing with salt

### Job Application Management
- **Complete CRUD**: Create, read, update, delete job applications
- **Status Tracking**: 9-state application lifecycle (discovered → offer/rejected)
- **Company Database**: Automatic company information extraction and storage
- **Notes System**: User annotations and application tracking
- **Analytics**: Summary statistics and performance metrics

### Resume Generation
- **AI Integration**: Multi-LLM support (OpenAI, Anthropic) with provider fallback
- **Job Analysis**: Automated requirement extraction from job descriptions
- **Template System**: Professional LaTeX templates with PDF compilation
- **Usage Limits**: Tier-based generation limits with verification requirements
- **File Management**: Secure storage and retrieval of generated resumes

### Event-Driven Architecture
- **Kafka Integration**: Asynchronous event publishing for scalability
- **Workflow Orchestration**: Multi-step job application processes
- **Agent System**: Specialized agents for scraping, analysis, generation, optimization
- **Future-Ready**: Event streams prepare for Phase 2+ worker separation

## 🏗️ Architecture & Design Patterns

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      API Component                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                FastAPI Application                  │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │ Routers │  │Dependencies│ │    Middleware    │  │   │
│  │  └────┬────┘  └─────┬────┘  └────────┬─────────┘  │   │
│  │       │             │                  │            │   │
│  │  ┌────┴──────────────┴─────────────────┴────────┐  │   │
│  │  │              Request Pipeline                 │  │   │
│  │  └───────────────────┬───────────────────────────┘  │   │
│  └──────────────────────┼───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┼───────────────────────────────┐   │
│  │                   Services Layer                     │   │
│  │  ┌─────────┐  ┌──────┴────┐  ┌─────────────────┐  │   │
│  │  │  Auth   │  │Application│  │    Generator    │  │   │
│  │  │ Service │  │  Service  │  │     Service     │  │   │
│  │  └────┬────┘  └─────┬─────┘  └────────┬────────┘  │   │
│  └───────┼──────────────┼─────────────────┼────────────┘   │
└──────────┼──────────────┼─────────────────┼─────────────────┘
           │              │                  │
    ┌──────┴───┐   ┌──────┴───┐      ┌──────┴───┐
    │PostgreSQL│   │  Redis   │      │  Kafka  │
    └──────────┘   └──────────┘      └──────────┘
```

### Design Patterns

#### 1. Dependency Injection
FastAPI's dependency injection system provides clean separation of concerns:
```python
@router.get("/applications/")
async def list_applications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Clean, testable endpoint with injected dependencies
```

#### 2. Chain of Responsibility
Authentication pipeline with progressive validation:
```python
get_current_user → get_current_active_user → get_verified_user → check_limits
```

#### 3. Factory Pattern
LLM provider selection and instantiation:
```python
LLMService.get_provider(provider_name) → OpenAIProvider | AnthropicProvider
```

#### 4. Event-Driven Architecture
All state changes emit events for asynchronous processing:
```python
Create Application → emit("application.created") → Trigger Workflows
```

## 📦 Dependencies

### Core Framework
```python
# FastAPI ecosystem
fastapi>=0.104.0          # Modern async web framework
uvicorn[standard]>=0.24.0 # ASGI server
pydantic>=2.0.0          # Data validation and settings

# Database
sqlalchemy>=2.0.0        # Async ORM
asyncpg>=0.29.0         # PostgreSQL async driver
alembic>=1.12.0         # Database migrations

# Authentication
python-jose[cryptography] # JWT token handling
passlib[bcrypt]          # Password hashing
python-multipart         # Form data parsing

# Event Streaming
aiokafka>=0.8.0         # Async Kafka client

# AI Integration
openai>=1.3.0           # OpenAI API client
anthropic>=0.7.0        # Anthropic API client

# Email Service
aiosmtplib>=2.0.0       # Async SMTP client
jinja2>=3.1.0           # Email templates
```

### External Services
- **PostgreSQL 13+**: Primary database with JSONB support
- **Redis 6+**: Caching and session storage
- **Kafka 2.8+**: Event streaming platform
- **SMTP Server**: Email verification (Gmail, SendGrid, etc.)

## 💻 Usage Examples

### Authentication Flow
```python
# Registration
POST /api/v1/auth/register
{
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
}

# Login
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secure_password

# Response
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}

# Email Verification
POST /api/v1/auth/verify-email
{
    "token": "verification_token_here"
}
```

### Job Application Management
```python
# Create Application
POST /api/v1/applications/
Authorization: Bearer <token>
{
    "company": "TechCorp",
    "position": "Senior Developer",
    "url": "https://techcorp.com/jobs/123",
    "job_description": "We are looking for...",
    "location": "San Francisco, CA",
    "remote": true,
    "salary_min": 120000,
    "salary_max": 150000
}

# List Applications with Filters
GET /api/v1/applications/?status=applied&company=TechCorp&skip=0&limit=20
Authorization: Bearer <token>

# Update Application Status
PATCH /api/v1/applications/123
Authorization: Bearer <token>
{
    "status": "interview",
    "notes": "Phone screening scheduled for next week"
}

# Get Analytics
GET /api/v1/applications/stats/summary
Authorization: Bearer <token>

# Response
{
    "total_applications": 45,
    "applications_this_week": 8,
    "by_status": {
        "applied": 12,
        "interview": 5,
        "rejected": 15,
        "offer": 2
    }
}
```

### Resume Generation
```python
# Analyze Job Description
POST /api/v1/generator/analyze-job
Authorization: Bearer <token>
Content-Type: application/json

"We are seeking a Python developer with FastAPI experience..."

# Response
{
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS", "React"],
    "experience_level": "Mid-level",
    "key_responsibilities": [...],
    "company_culture": [...]
}

# Generate Custom Resume
POST /api/v1/generator/generate-resume
Authorization: Bearer <token>
{
    "job_id": 123,
    "template": "modern_professional"
}

# Check Available LLM Providers
GET /api/v1/generator/llm-providers
Authorization: Bearer <token>

# Response
{
    "available_providers": ["openai", "anthropic"],
    "default_provider": "openai",
    "configured": {
        "openai": true,
        "anthropic": true
    }
}
```

### File Operations
```python
# Upload Resume
POST /api/v1/files/upload/resume
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=@resume.pdf&job_application_id=123

# List User Files
GET /api/v1/files/list?file_type=resumes&limit=20
Authorization: Bearer <token>

# Get Download URL
GET /api/v1/files/download-url/resumes/user123/resume_v2.pdf
Authorization: Bearer <token>

# Response
{
    "url": "https://storage.example.com/presigned-url...",
    "expires_in": 3600
}
```

## 📡 API Reference

### Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Authenticate user | No |
| POST | `/api/v1/auth/verify-email` | Verify email address | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |
| GET | `/api/v1/auth/me/usage` | Get usage statistics | Yes |
| DELETE | `/api/v1/auth/delete-test-user` | Delete test user | No* |

### Application Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/applications/` | List applications | Yes |
| POST | `/api/v1/applications/` | Create application | Yes (Verified) |
| GET | `/api/v1/applications/{id}` | Get specific application | Yes |
| PATCH | `/api/v1/applications/{id}` | Update application | Yes |
| DELETE | `/api/v1/applications/{id}` | Delete application | Yes |
| GET | `/api/v1/applications/stats/summary` | Get statistics | Yes |
| POST | `/api/v1/applications/{id}/notes` | Add note | Yes |

### Resume Generation
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/generator/llm-providers` | List AI providers | Yes |
| POST | `/api/v1/generator/analyze-job` | Analyze job description | Yes |
| POST | `/api/v1/generator/generate-resume` | Generate resume | Yes (Limits) |

### File Operations
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/files/upload/resume` | Upload resume file | Yes |
| GET | `/api/v1/files/list` | List user files | Yes |
| GET | `/api/v1/files/download-url/{key}` | Get download URL | Yes |
| DELETE | `/api/v1/files/{key}` | Delete file | Yes |

### System Health
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Root endpoint | No |
| GET | `/health` | Health check | No |
| GET | `/docs` | API documentation | No |

*Only allows deletion of `yodalives@gmail.com` test user

## ⚙️ Configuration

### Environment Variables
```bash
# Core Settings
PROJECT_NAME="Resume Automation Platform"
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_PREFIX=/api/v1

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/resume_automation
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/resume_automation

# Cache & Sessions
REDIS_URL=redis://localhost:6379

# Event Streaming
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# AI Providers (at least one required)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
DEFAULT_LLM_PROVIDER=openai

# Email Service (optional - graceful fallback)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=ResumeAI Platform

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3080", "http://localhost:8000"]

# File Upload Limits
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=[".pdf", ".doc", ".docx", ".txt"]
```

### Subscription Tier Limits
```python
TIER_LIMITS = {
    "free": {
        "monthly_applications": 50,
        "monthly_resumes": 20,
        "can_use_auto_apply": False,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": 25,
    },
    "professional": {
        "monthly_applications": 1000,
        "monthly_resumes": 500,
        "can_use_auto_apply": True,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": 500,
    },
    # ... other tiers
}
```

## 🛠️ Development Notes

### Local Development Setup
```bash
# 1. Clone repository and setup environment
python -m venv venv
source venv/bin/activate
poetry env use venv/bin/python
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start external services
docker-compose up -d postgres redis zookeeper kafka

# 4. Run database migrations
poetry run alembic upgrade head

# 5. Start API server
poetry run uvicorn src.api.main:app --reload
# OR use