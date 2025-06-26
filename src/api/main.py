# src/api/main.py
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import settings
from src.core.database import engine
from src.core.kafka_client import cleanup_event_producer
from src.api.routers import applications, auth, generator, files


async def check_database_connection(engine: AsyncEngine) -> bool:
    """Test database connection on startup"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if PostgreSQL is running: docker-compose ps")
        print("   2. Start PostgreSQL if needed: docker-compose up -d postgres")
        print(f"   3. Check DATABASE_URL in .env: {settings.database_url}")
        return False


async def check_redis_connection() -> bool:
    """Test Redis connection on startup (optional)"""
    try:
        import redis.asyncio as redis  # Import here
        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.close()
        print("✅ Redis connection successful")
        return True
    except ImportError:
        print("⚠️  Redis client not installed (pip install redis)")
        return True
    except Exception as e:
        print(f"⚠️  Redis connection failed (non-critical): {str(e)}")
        return True


async def check_kafka_connection() -> bool:
    """Test Kafka connection on startup (optional)"""
    try:
        from src.core.kafka_client import get_event_producer
        producer = await get_event_producer()
        print("✅ Kafka connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Kafka connection failed (non-critical): {str(e)}")
        return True


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Handle startup and shutdown events"""
    # Startup
    print(f"\n🚀 Starting {settings.project_name}...")
    
    # Critical checks (fail if these don't pass)
    if not await check_database_connection(engine):
        print("\n❌ Startup aborted: Database connection required")
        sys.exit(1)
    
    # Optional checks (log but don't fail)
    if settings.redis_url:
        await check_redis_connection()
    
    # Check Kafka connection
    await check_kafka_connection()
    
    print(f"\n✅ API ready at http://localhost:{settings.port or 8048}")
    print(f"📚 Documentation at http://localhost:{settings.port or 8048}/docs")
    print(f"🎛️ Kafka UI at http://localhost:9080\n")
    
    yield
    
    # Shutdown
    print("\n👋 Gracefully shutting down...")
    await cleanup_event_producer()


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],  # Use settings for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["authentication"]
)

app.include_router(
    applications.router, 
    prefix=f"{settings.api_v1_prefix}/applications",
    tags=["applications"]
)

app.include_router(
    generator.router, 
    prefix=f"{settings.api_v1_prefix}/generator",
    tags=["generator"]
)

app.include_router(
    files.router,
    prefix=f"{settings.api_v1_prefix}/files",
    tags=["files"]
)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": settings.project_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    health_status = {"status": "healthy", "services": {}}
    
    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis if configured
    if settings.redis_url:
        try:
            import redis.asyncio as redis
            client = redis.from_url(settings.redis_url)
            await client.ping()
            await client.close()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
    
    # Check Kafka connection
    try:
        from src.core.kafka_client import get_event_producer
        producer = await get_event_producer()
        health_status["services"]["kafka"] = "healthy"
    except Exception as e:
        health_status["services"]["kafka"] = f"unhealthy: {str(e)}"
    
    return health_status
