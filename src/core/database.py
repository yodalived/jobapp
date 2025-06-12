# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import settings

# Async engine for FastAPI
engine = create_async_engine(settings.async_database_url)
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
        yield session
