import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.api.dependencies import (
    get_audit_service,
    get_rw_client,
    get_uow_factory,
)
from app.core import UnitOfWork
from app.db.models import Client
from app.db.models.base import Base
from app.integrations.remnawave import RemnaWaveClient
from app.main import app
from app.services import ClientService
from app.services.audit import AuditService


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


@pytest_asyncio.fixture
def uow_factory(db_session):
    session_factory = async_sessionmaker(
        bind=db_session.bind,
        expire_on_commit=False,
    )

    def _factory():
        return UnitOfWork(session_factory)

    return _factory     # lambda: UnitOfWork(session_factory)


@pytest.fixture
def audit_service(db_session):
    session_factory = async_sessionmaker(
        bind=db_session.bind,
        expire_on_commit=False,
    )
    return AuditService(session_factory)


@pytest.fixture
def service(uow_factory, rw_client, audit_service):
    return ClientService(
        uow_factory=uow_factory,
        rw_client=rw_client,
        audit_service=audit_service,
    )


@pytest_asyncio.fixture
async def client(db_session):
    client = Client(
        remnawave_uuid=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(client)
    await db_session.commit()
    return client


# @pytest_asyncio.fixture(autouse=True)
# async def clean_db(engine):
#     '''Очищает таблицы между тестами.
#
#     На случай использования engine с разными сессиями в uow_factory и audit_service.
#     '''
#     async with engine.begin() as conn:
#         for table in reversed(Base.metadata.sorted_tables):
#             await conn.execute(table.delete())


@pytest_asyncio.fixture
async def api_client(uow_factory, rw_client, audit_service):
    app.dependency_overrides[get_uow_factory] = lambda: uow_factory
    app.dependency_overrides[get_rw_client] = lambda: rw_client
    app.dependency_overrides[get_audit_service] = lambda: audit_service

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url='http://test',
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
