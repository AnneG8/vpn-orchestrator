import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.db.models.base import Base
from app.integrations.remnawave import RemnaWaveClient


@pytest.fixture(scope='session')
def postgres_container():
    with PostgresContainer('postgres:16') as postgres:
        yield postgres


@pytest_asyncio.fixture(scope='session')
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()

    async_url = sync_url.replace(
        'postgresql+psycopg2://',
        'postgresql+asyncpg://',
    )

    engine = create_async_engine(async_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    connection = await engine.connect()
    transaction = await connection.begin()

    async_session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    session = async_session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
def mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        raise NotImplementedError('Mock not configured')
    return httpx.MockTransport(handler)


@pytest.fixture
def rw_client(mock_transport):
    http_client = httpx.AsyncClient(
        transport=mock_transport,
        base_url='http://test',
    )
    client = RemnaWaveClient(http_client)
    return client
