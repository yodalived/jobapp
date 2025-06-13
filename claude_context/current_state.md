# Current State of Resume Automation Project

## What's Working
- Database with user support and multi-tenancy
- Full CRUD API with authentication
- JWT-based authentication system
- User registration and login
- Row-level security (users see only their data)
- Subscription tiers with limits
- Health monitoring
- Auto-generated API docs

## Authentication Flow
1. Register: POST /api/v1/auth/register
2. Login: POST /api/v1/auth/login (returns JWT token)
3. Use token: Authorization: Bearer YOUR_TOKEN

## File Structure
src/
├── api/
│   ├── main.py              ✅ FastAPI app with auth router
│   ├── models/
│   │   ├── schema.py        ✅ SQLAlchemy models (with user_id)
│   │   ├── schemas.py       ✅ Pydantic models
│   │   ├── auth.py          ✅ User model with SaaS features
│   │   └── auth_schemas.py  ✅ Auth Pydantic schemas
│   ├── routers/
│   │   ├── applications.py  ✅ CRUD endpoints (auth required)
│   │   └── auth.py          ✅ Login/register endpoints
│   └── dependencies.py      ✅ get_current_user dependency
├── core/
│   ├── config.py            ✅ Settings
│   ├── database.py          ✅ Async/sync engines
│   └── auth.py              ✅ Password hashing, JWT

## Subscription Tiers & Limits
FREE: 50 applications/month, 20 resumes/month
STARTER: 200 applications/month, 100 resumes/month
PROFESSIONAL: 1000 applications/month, 500 resumes/month, auto-apply
ENTERPRISE: Unlimited everything

## Required Packages
All installed via: poetry add "python-jose[cryptography]" passlib bcrypt python-multipart

## How to Test
# Register
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=password123"

# Use protected endpoint
export TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/applications/
