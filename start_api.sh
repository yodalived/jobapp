#!/bin/bash

echo "🔍 Checking services..."

# Check if PostgreSQL is running
if ! docker ps | grep -q postgresql; then
    echo "❌ PostgreSQL is not running!"
    echo "🚀 Starting PostgreSQL..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 3
fi

# Check if Redis is running
if ! docker ps | grep -q redis; then
    echo "⚠️  Redis is not running!"
    echo "🚀 Starting Redis..."
    docker-compose up -d redis
fi

# Check if PostgreSQL is actually accepting connections
echo "🔗 Testing PostgreSQL connection..."
docker exec postgresql pg_isready -U postgres -d resume_db

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready!"
else
    echo "❌ PostgreSQL is not accepting connections yet."
    echo "⏳ Waiting a bit more..."
    sleep 5
fi

echo "🚀 Starting API..."
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8048
