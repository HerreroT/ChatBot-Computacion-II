"""Configuración de sesión de base de datos."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.common.config import settings


# Motor async de SQLAlchemy
engine = create_async_engine(
    settings.DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Sesión async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Obtiene una sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()





