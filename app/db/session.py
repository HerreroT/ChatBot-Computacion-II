from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

min_size = max(settings.db_pool_min_size, 1)
max_size = max(settings.db_pool_max_size, min_size)
max_overflow = max(max_size - min_size, 0)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=min_size,
    max_overflow=max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
