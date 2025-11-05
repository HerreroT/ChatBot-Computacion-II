"""Configuración de pytest."""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models import Base

# Base de datos de prueba
TEST_DB_URL = "mysql+aiomysql://root:password@localhost:3306/barber_test"


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Engine de prueba."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Sesión de base de datos de prueba."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client():
    """Cliente HTTP de prueba."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac





