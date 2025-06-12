# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings

# Async engine for FastAPI with connection pooling settings
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,         # Number of connections to maintain
    max_overflow=10,     # Maximum overflow connections
    pool_timeout=30,     # Timeout before giving up on getting a connection
    echo=False,          # Set to True for SQL query logging
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Sync engine for Alembic migrations
sync_engine = create_engine(settings.database_url)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
