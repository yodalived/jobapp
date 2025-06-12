# Quick Command Reference

## Start Development
source venv/bin/activate
docker-compose up -d postgres redis
poetry run uvicorn src.api.main:app --reload

## Test API
# Create application
curl -X POST "http://localhost:8000/api/v1/applications/" -H "Content-Type: application/json" -d '{"company": "Test Corp", "position": "Engineer", "url": "https://test.com/job/1"}'

# List all
curl "http://localhost:8000/api/v1/applications/"

# Update status
curl -X PATCH "http://localhost:8000/api/v1/applications/1" -H "Content-Type: application/json" -d '{"status": "applied"}'

## Database
# Connect to PostgreSQL
docker exec -it postgresql psql -U postgres -d resume_db

# Common queries
SELECT * FROM job_applications;
SELECT status, COUNT(*) FROM job_applications GROUP BY status;

## Git
git add -A
git commit -m "feat: Add job application CRUD endpoints"
git status

## Docker
docker-compose ps
docker-compose logs -f api
docker-compose down
