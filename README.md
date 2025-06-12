# Resume Automation System

An automated resume generation and job application tracking system built with Python, FastAPI, and PostgreSQL.

## Features (Planned)

- 🤖 Automated job discovery from LinkedIn, Indeed, and other platforms
- 📄 AI-powered resume customization for each job application  
- 📊 Application tracking with success analytics
- 🎯 Smart job matching based on your profile
- 📈 Learning system that improves over time

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery
- **Database**: PostgreSQL, Redis
- **Scraping**: Playwright, BeautifulSoup4
- **AI/ML**: LangChain, OpenAI API
- **Deployment**: Docker, Kubernetes

## Quick Start

1. Clone the repository
   git clone <your-repo-url>
   cd resume-automation

2. Set up Python environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install poetry
   poetry install

3. Copy environment variables
   cp .env.example .env
   # Edit .env with your settings

4. Start services
   docker-compose up -d postgres redis

5. Run migrations
   poetry run alembic upgrade head

6. Start the API
   poetry run uvicorn src.api.main:app --reload

7. View API documentation
   Open http://localhost:8000/docs in your browser

## Project Structure

src/
├── api/         # FastAPI application and routers
├── core/        # Core configuration and database
├── scraper/     # Job scraping modules
├── generator/   # Resume generation
├── ml/          # Machine learning and analytics
└── worker/      # Background task processing

## Development

See claude_context/ directory for detailed documentation and development guides.

## License

[Your License]
