# Current Code Structure

## Directory Layout
resume-automation/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app (TO BE CREATED)
│   │   ├── routers/
│   │   │   └── __init__.py
│   │   └── models/
│   │       └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # CREATED - Settings management
│   │   └── database.py          # CREATED - DB connection
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── (future: linkedin.py, indeed.py, etc.)
│   ├── generator/
│   │   ├── __init__.py
│   │   └── templates/
│   │       └── (future: resume.tex)
│   ├── ml/
│   │   ├── __init__.py
│   │   └── (future: scorer.py, analyzer.py)
│   └── worker/
│       ├── __init__.py
│       └── (future: tasks.py)
├── tests/
├── k8s/
│   ├── base/
│   ├── dev/
│   └── prod/
├── docker/
├── claude_context/              # Documentation for context
│   ├── architecture.md
│   ├── current_code_structure.md
│   ├── next_session_template.md
│   └── development_commands.md
├── venv/                        # Python virtual environment
├── .env                         # Local environment variables
├── .env.example                 # Template for .env
├── .gitignore                   # Git ignore file
├── pyproject.toml              # Poetry configuration
├── poetry.lock                 # Locked dependencies
├── PROJECT_STATUS.md           # Current project status
└── README.md                   # Project readme

## Created Files Content

### src/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    async_database_url: str
    
    # Redis
    redis_url: str
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Resume Automation"
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    
    # LinkedIn
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Scraping
    scrape_interval_hours: int = 6
    max_applications_per_day: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
