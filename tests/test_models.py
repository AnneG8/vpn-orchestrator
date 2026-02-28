from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import Client, Operation
from app.db.models.enums import OperationAction, OperationResult


@pytest.mark.asyncio
async def test_create_client(db_session):
    client = Client(
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )

    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)

    assert client.id is not None
    assert client.status.value == 'active'


@pytest.mark.asyncio
async def test_create_operation(db_session):
    client = Client(
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)

    operation = Operation(
        client_id=client.id,
        action=OperationAction.CREATE_CLIENT,
        payload={'test_key': 'test_value'},
        result=OperationResult.SUCCESS,
    )

    db_session.add(operation)
    await db_session.commit()
    await db_session.refresh(operation)

    assert operation.id is not None
    assert operation.client_id == client.id
    assert operation.result == OperationResult.SUCCESS
