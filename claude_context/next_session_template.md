## 4. claude_context/next_session_template.md

```markdown
# Template for Starting Next Claude Session

## Opening Message Template

I'm continuing work on my resume automation system in Python. Here's the current status:

**Project**: Automated resume generation and job application tracking system

**Current Structure**:
resume-automation/
├── src/
│   ├── api/         # FastAPI application
│   ├── core/        # Config and database setup
│   ├── scraper/     # Job scraping (Playwright)
│   ├── generator/   # Resume generation (LaTeX)
│   ├── ml/          # Learning/analytics
│   └── worker/      # Celery tasks

￼

**Completed**:
- Project structure
- Dependencies (Poetry)
- PostgreSQL & Redis (Docker)
- config.py and database.py
- Environment setup

**Tech Stack**:
- FastAPI (async API)
- PostgreSQL + SQLAlchemy
- Redis + Celery
- Playwright (scraping)
- LangChain + OpenAI

**Current Task**: [FILL IN CURRENT TASK]

**Specific Question**: [FILL IN SPECIFIC QUESTION]

[PASTE RELEVANT CODE OR ERROR]

## Key Context Points to Mention

1. Building Python-only (no Go)
2. Have existing K8s cluster for deployment
3. Starting with LinkedIn Easy Apply
4. Using LaTeX templates for resumes
5. Want learning system with RAG

## If You Need to Share Code State

```python
# Current working file: src/[path/to/file.py]
[PASTE CURRENT CODE]

If You Hit an Error
Error occurred in: [file and function]
Error message:
[PASTE FULL ERROR]

What I tried:
1. [What you attempted]
2. [Other solutions tried]
