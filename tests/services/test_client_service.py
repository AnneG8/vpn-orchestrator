import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select

from app.db.models import Client, Operation
from app.db.models.enums import ClientStatus, OperationAction, OperationResult
from tests.integrations.test_remnawave_client import build_response


async def check_operation(
        db_session,
        action: OperationAction,
        result: OperationResult = OperationResult.SUCCESS,
        client: Client | None = None
):
    res = await db_session.execute(select(Operation))
    operations = res.scalars().all()

    assert len(operations) == 1
    if client is not None:
        assert operations[0].client_id == client.id
    assert operations[0].action is action
    assert operations[0].result is result


@pytest.mark.asyncio
async def test_create_client(service, rw_client, db_session):
    username = 'test_user'
    user_uuid = uuid.uuid4()
    days = 30
    expire_at = datetime.now(timezone.utc) + timedelta(days=days)

    def handler(request: httpx.Request) -> httpx.Response:
        response_json = build_response(
            uuid=str(user_uuid),
            username=username,
            expireAt=expire_at.isoformat(),
        )

        return httpx.Response(201, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    client_id = await service.create_client(
        username=username,
        days=days,
    )

    client = await db_session.get(Client, client_id)
    assert client is not None
    assert client.remnawave_uuid == user_uuid
    assert client.expires_at == expire_at

    await check_operation(
        db_session,
        action=OperationAction.CREATE_CLIENT,
        client=client,
    )


async def test_create_client_error(service, rw_client, db_session):
    def handler(request):
        return httpx.Response(400, json={'message': 'error'})

    rw_client._client._transport = httpx.MockTransport(handler)

    with pytest.raises(Exception):
        await service.create_client(
            username='test_user',
            days=30,
        )

    await check_operation(
        db_session,
        action=OperationAction.CREATE_CLIENT,
        result=OperationResult.FAIL,
    )


@pytest.mark.asyncio
async def test_get_client(service, client):
    new_client = await service.get_client(client_id=client.id)

    assert client.id == new_client.id


@pytest.mark.asyncio
async def test_list_clients(service, client):
    clients = await service.list_clients(
        status=ClientStatus.ACTIVE,
        expired=False,
    )

    assert len(clients) == 1
    assert clients[0].id == client.id


@pytest.mark.asyncio
async def test_extend_subscription(service, rw_client, db_session, client):
    days = 30
    new_expiration = client.expires_at + timedelta(days=days)

    def handler(request: httpx.Request):
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            expireAt=new_expiration.isoformat(),
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    await service.extend_subscription(
        client_id=client.id,
        days=days,
    )

    await db_session.refresh(client)
    assert client.expires_at == new_expiration
    await check_operation(
        db_session,
        action=OperationAction.EXTEND_SUBSCRIPTION,
        client=client,
    )


@pytest.mark.asyncio
async def test_change_client_status(service, rw_client, db_session, client):
    def handler(request: httpx.Request):
        return httpx.Response(200, json={})

    rw_client._client._transport = httpx.MockTransport(handler)

    await service.block_client(client_id=client.id)

    await db_session.refresh(client)
    assert client.status is ClientStatus.DISABLED
    await check_operation(
        db_session,
        action=OperationAction.BLOCK,
        client=client,
    )

    await db_session.execute(Operation.__table__.delete())
    await db_session.flush()

    await service.unblock_client(client_id=client.id)

    await db_session.refresh(client)
    assert client.status is ClientStatus.ACTIVE
    await check_operation(
        db_session,
        action=OperationAction.UNBLOCK,
        client=client,
    )

    await db_session.execute(Operation.__table__.delete())
    await db_session.flush()

    await service.archive_client(client_id=client.id)

    await db_session.refresh(client)
    assert client.status is ClientStatus.ARCHIVED
    await check_operation(
        db_session,
        action=OperationAction.ARCHIVE_CLIENT,
        client=client,
    )


@pytest.mark.asyncio
async def test_get_config(service, rw_client, db_session, client):
    sub_url = 'https://test/sub/test_url'

    def handler(request: httpx.Request):
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            subscriptionUrl=sub_url,
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await service.get_config(client_id=client.id)

    assert result == sub_url
    await check_operation(
        db_session,
        action=OperationAction.GET_CONFIG,
        client=client,
    )


@pytest.mark.asyncio
async def test_rotate_config(service, rw_client, db_session, client):
    new_sub_url = 'https://test/sub/new_test_url'

    def handler(request: httpx.Request):
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            subscriptionUrl=new_sub_url,
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await service.rotate_config(client_id=client.id)

    assert result == new_sub_url
    await check_operation(
        db_session,
        action=OperationAction.ROTATE_CONFIG,
        client=client,
    )
