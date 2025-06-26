# Troubleshooting Guide

Common issues and their solutions for the resume automation system.

## Quick Health Check

**First things to check when something isn't working:**

```bash
# 1. Run full system test
python test-scripts/test_resume_generation.py

# 2. Check API endpoints  
python test-scripts/test_all_endpoints.py

# 3. Verify git status
git status

# 4. Check recent changes
git log --oneline -5
```

## Common Issues

### 1. LaTeX Compilation Failures

**Symptoms**: 
- Error: "LaTeX compilation failed"
- PDFs not generating
- Special character errors in logs

**Likely Causes**:
- Unescaped special characters in user content
- Missing pdflatex installation
- Corrupted template files

**Solutions**:
```bash
# Check if pdflatex is installed
pdflatex --version

# Test LaTeX escaping
python test-scripts/test_latex_escaping.py

# Check generated LaTeX content
ls resume_outputs/*.tex
cat resume_outputs/test_customized.tex  # Look for unescaped characters
```

**Prevention**:
- Always use `|latex_escape` filter in templates for user content
- Test with special characters: `&`, `%`, `$`, `#`, `^`, `_`, `{`, `}`, `~`
- Don't escape template LaTeX structure, only dynamic content

### 2. OpenAI/Anthropic API Failures

**Symptoms**:
- "API key not configured" errors
- AI customization tests failing
- Network timeout errors

**Likely Causes**:
- Missing or invalid API keys
- Rate limiting
- Network connectivity issues
- Using deprecated API methods

**Solutions**:
```bash
# Check if API keys are set
echo $OPENAI_API_KEY | cut -c1-10     # Should show first 10 chars
echo $ANTHROPIC_API_KEY | cut -c1-10  # Should show first 10 chars

# Test LLM providers directly
python -c "
from src.generator.llm_interface import LLMService
import asyncio
async def test():
    llm = LLMService()
    print('Available providers:', llm.get_available_providers())
    if llm.get_available_providers():
        result = await llm.generate('Hello world', provider='openai')
        print('Test result:', result[:50])
asyncio.run(test())
"
```

**Prevention**:
- Keep API keys in `.env` file, not in code
- Use `LLMService` with provider fallback
- Handle API errors gracefully with try/catch
- Monitor usage and rate limits

### 3. Database Connection Issues

**Symptoms**:
- "Database connection failed" on startup
- SQLAlchemy connection errors
- Migration failures

**Likely Causes**:
- PostgreSQL not running
- Wrong connection string
- Database doesn't exist
- Permissions issues

**Solutions**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL if needed
docker-compose up -d postgres

# Test connection manually
docker exec postgresql pg_isready -U postgres -d resume_db

# Check connection string
echo $DATABASE_URL

# Run migrations
poetry run alembic upgrade head
```

**Prevention**:
- Use `docker-compose up -d postgres` for consistent setup
- Verify database URL format: `postgresql+asyncpg://user:pass@host/db`
- Run migrations before starting API

### 4. File Permission/Path Issues

**Symptoms**:
- "Permission denied" errors
- "File not found" errors
- PDF files not created in expected location

**Likely Causes**:
- Incorrect file paths (relative vs absolute)
- Cross-device file operations
- Permission issues in output directory

**Solutions**:
```bash
# Check output directory permissions
ls -la resume_outputs/

# Create output directory if missing
mkdir -p resume_outputs

# Test file operations
touch resume_outputs/test.txt && rm resume_outputs/test.txt
```

**Prevention**:
- Always use absolute paths for file operations
- Use `shutil.move()` instead of `rename()` for cross-device moves
- Ensure output directories exist and are writable

### 5. Import/Module Errors

**Symptoms**:
- "ModuleNotFoundError" 
- "ImportError: cannot import name"
- Circular import errors

**Likely Causes**:
- Missing dependencies
- Incorrect Python path
- Circular imports
- Virtual environment not activated

**Solutions**:
```bash
# Check virtual environment
which python
pip list | grep fastapi

# Install missing dependencies
poetry install

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test imports manually
python -c "from src.generator.resume_generator import ResumeGenerator; print('OK')"
```

**Prevention**:
- Always run `poetry install` after pulling changes
- Use relative imports within the project
- Avoid circular imports by restructuring dependencies

### 6. Test Failures

**Symptoms**:
- Tests failing that previously passed
- Inconsistent test results
- API endpoint tests failing

**Likely Causes**:
- Database state issues
- Missing test dependencies
- Environment variable issues
- API rate limiting

**Solutions**:
```bash
# Reset test environment
docker-compose down && docker-compose up -d postgres
poetry run alembic upgrade head

# Check test environment variables
cat .env | grep -E "(API_KEY|DATABASE_URL)"

# Run tests individually
python test-scripts/test_resume_generation.py
python test-scripts/test_all_endpoints.py
python test-scripts/test_latex_escaping.py
```

**Prevention**:
- Ensure tests can run independently
- Use test database if available
- Don't rely on specific data state
- Handle API rate limits gracefully

## Environment-Specific Issues

### Docker/Container Issues

**Symptoms**:
- Services not starting
- Port conflicts
- Volume mount issues

**Solutions**:
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose restart postgres
```

### Development vs Production

**Common Differences**:
- File paths (absolute vs relative)
- Environment variables
- Service availability
- Permissions

**Solutions**:
- Use environment-specific configuration
- Test in production-like environment
- Document environment differences

## Debug Information Collection

### When Reporting Issues

Always include:

```bash
# System information
python --version
poetry --version
docker --version

# Service status
docker-compose ps
poetry run alembic current

# Recent changes
git log --oneline -5
git status

# Test results
python test-scripts/test_resume_generation.py 2>&1

# Environment (without secrets)
env | grep -E "(DATABASE|REDIS|LLM)" | sed 's/=.*/=***/'
```

### Log Locations

- **API Logs**: Console output from uvicorn
- **Database Logs**: `docker-compose logs postgres`
- **Test Output**: Console output from test scripts
- **LaTeX Logs**: Temporary files during PDF generation

## Recovery Procedures

### Hard Reset

If everything is broken:

```bash
# 1. Stop all services
docker-compose down

# 2. Reset database
docker-compose up -d postgres
poetry run alembic upgrade head

# 3. Verify tests
python test-scripts/test_resume_generation.py

# 4. Check git status
git status
```

### Partial Reset

If only specific component broken:

```bash
# Database only
docker-compose restart postgres
poetry run alembic upgrade head

# API only  
pkill -f uvicorn
poetry run uvicorn src.api.main:app --reload

# Dependencies only
poetry install
```

---

## Prevention Checklist

**Before making changes:**
- [ ] Run full test suite
- [ ] Check git status
- [ ] Backup working state

**During development:**
- [ ] Test changes incrementally
- [ ] Use comprehensive error handling
- [ ] Follow established patterns

**After changes:**
- [ ] Run all tests again
- [ ] Update documentation
- [ ] Commit working state

**Before ending session:**
- [ ] Document current state
- [ ] Note any issues found
- [ ] Update troubleshooting guide if needed
- [ ] Ensure all text files end with carriage return (<cr>)