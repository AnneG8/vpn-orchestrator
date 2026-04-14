import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.db.models.base import Base


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
