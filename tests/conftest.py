import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from database import Base, engine, async_session
from sqlalchemy.ext.asyncio import AsyncSession

# Python жолына жобаның түбір жолын қосу (модульдерді табу үшін)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Async тесттер үшін қажетті backend
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# Тестке дейін база құрылымын жаңарту
@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

# HTTP клиент фикстурасы (тесттерде client деп қолдануға болады)
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# База сессия фикстурасы
@pytest.fixture
async def db_session() -> AsyncSession:
    async with async_session() as session:
        yield session