# API Endpoints Reference

## Authentication Required
All endpoints except /health, /docs, /register, and /login require Bearer token authentication:
Authorization: Bearer <token>

## Endpoint Details

### Health Check
GET /health
Response: {
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}

### Authentication
POST /api/v1/auth/register
Body: {"email": "user@example.com", "password": "password123"}

POST /api/v1/auth/login
Body: username=user@example.com&password=password123
Response: {"access_token": "...", "token_type": "bearer"}

GET /api/v1/auth/me
Response: User profile with subscription info

GET /api/v1/auth/me/usage
Response: Usage stats and tier limits

### Job Applications
POST /api/v1/applications/
Body: {
  "company": "string",
  "position": "string",
  "url": "string",
  "job_description": "string",
  "status": "interested|applied|interviewing|rejected|offer",
  "job_type": "technical|management|other",
  "location": "string",
  "remote": boolean,
  "salary_min": number,
  "salary_max": number
}

GET /api/v1/applications/
Query params: skip, limit, status, job_type

GET /api/v1/applications/{id}
PATCH /api/v1/applications/{id}
DELETE /api/v1/applications/{id}

POST /api/v1/applications/{id}/notes
Body: {"note": "string"}

GET /api/v1/applications/stats/summary
Response: Application statistics

### Generator
GET /api/v1/generator/llm-providers
Response: Available LLM providers and configuration

POST /api/v1/generator/analyze-job?job_description=...
Query param: job_description
Response: Extracted skills and requirements

POST /api/v1/generator/generate-customized
Body: {
  "application_id": number,
  "master_resume_data": {...},
  "customize_with_ai": boolean,
  "provider": "openai|anthropic|auto"
}

POST /api/v1/generator/generate
Body: {
  "application_id": number,
  "resume_data": {...},
  "template_name": "modern_professional"
}

GET /api/v1/generator/example-data
Response: Example resume data structure

GET /api/v1/generator/templates
Response: Available LaTeX templates
