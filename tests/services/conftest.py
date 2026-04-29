import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import UnitOfWork
from app.db.models import Client
from app.services import ClientService
from app.services.audit import AuditService


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
