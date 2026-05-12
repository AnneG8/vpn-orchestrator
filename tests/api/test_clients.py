import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from httpx import Response

from app.api.schemas import (
    ClientResponse,
    ClientsListResponse,
    CreateClientResponse,
)
from app.db.models import Client
from app.db.models.enums import ClientStatus, OperationAction, OperationResult
from tests.integrations.test_remnawave_client import build_response
from tests.services.test_client_service import check_operation


@pytest.mark.asyncio
async def test_create_client(api_client, rw_client, db_session):
    username = 'test_user'
    user_uuid = uuid.uuid4()
    days = 30
    expire_at = datetime.now(timezone.utc) + timedelta(days=days)

    def handler(request: httpx.Request):
        response_json = build_response(
            uuid=str(user_uuid),
            username=username,
            expireAt=expire_at.isoformat(),
        )
        return httpx.Response(201, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    response: Response = await api_client.post(
        '/api/clients',
        json={
            'username': username,
            'days': days,
        },
    )

    assert response.status_code == 201

    data = response.json()
    parsed = CreateClientResponse.model_validate(data)

    client = await db_session.get(Client, parsed.id)
    assert client is not None
    assert client.remnawave_uuid == user_uuid
    assert client.expires_at == expire_at

    await check_operation(
        db_session,
        action=OperationAction.CREATE_CLIENT,
        client=client,
    )


@pytest.mark.asyncio
async def test_get_client(api_client, client):
    response = await api_client.get(f'/api/clients/{client.id}')

    assert response.status_code == 200

    data = response.json()
    parsed = ClientResponse.model_validate(data)

    assert parsed.id == client.id


@pytest.mark.asyncio
async def test_get_client_not_found(api_client):
    response = await api_client.get(f'/api/clients/{uuid.uuid4()}')

    assert response.status_code == 404

    data = response.json()

    assert data.get('type') == 'client_not_found'


@pytest.mark.asyncio
async def test_list_clients(api_client, client):
    response = await api_client.get('/api/clients')

    assert response.status_code == 200

    data = response.json()
    parsed = ClientsListResponse.model_validate(data)

    assert len(parsed.items) == 1
    assert parsed.items[0].id == client.id
    assert parsed.next_cursor == client.created_at


@pytest.mark.asyncio
async def test_extend_subscription(api_client, rw_client, db_session, client):
    days = 30
    new_expiration = client.expires_at + timedelta(days=days)

    def handler(request: httpx.Request):
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            expireAt=new_expiration.isoformat(),
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.post(
        f'/api/clients/{client.id}/extend',
        json={'days': days},
    )

    assert response.status_code == 204

    await db_session.refresh(client)
    assert client.expires_at == new_expiration
    await check_operation(
        db_session,
        action=OperationAction.EXTEND_SUBSCRIPTION,
        client=client,
    )


async def change_client_status(
        api_client,
        rw_client,
        db_session,
        client,
        action: OperationAction,
        new_status: ClientStatus,
        api_url,
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.post(api_url)

    assert response.status_code == 204

    await db_session.refresh(client)
    assert client.status is new_status
    await check_operation(
        db_session,
        action=action,
        client=client,
    )


@pytest.mark.asyncio
async def test_block_client(api_client, rw_client, db_session, client):
    url = f'/api/clients/{client.id}/block'
    await change_client_status(
        api_client,
        rw_client,
        db_session,
        client,
        action=OperationAction.BLOCK,
        new_status=ClientStatus.DISABLED,
        api_url=url,
    )


@pytest.mark.asyncio
async def test_unblock_client(api_client, rw_client, db_session, client):
    url = f'/api/clients/{client.id}/unblock'
    await change_client_status(
        api_client,
        rw_client,
        db_session,
        client,
        action=OperationAction.UNBLOCK,
        new_status=ClientStatus.ACTIVE,
        api_url=url,
    )


@pytest.mark.asyncio
async def test_archive_client(api_client, rw_client, db_session, client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.delete(
        f'/api/clients/{client.id}',
    )

    assert response.status_code == 204
    await db_session.refresh(client)
    assert client.status is ClientStatus.ARCHIVED
    await check_operation(
        db_session,
        action=OperationAction.ARCHIVE_CLIENT,
        client=client,
    )


@pytest.mark.asyncio
async def test_get_config(api_client, rw_client, client):
    sub_url = 'https://test/sub/test_url'

    def handler(request: httpx.Request) -> httpx.Response:
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            subscriptionUrl=sub_url,
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.get(
        f'/api/clients/{client.id}/config',
    )

    assert response.status_code == 200
    assert response.json() == {'config': sub_url}


@pytest.mark.asyncio
async def test_rotate_config(api_client, rw_client, client):
    new_sub_url = 'https://test/sub/new_test_url'

    def handler(request: httpx.Request) -> httpx.Response:
        response_json = build_response(
            uuid=str(client.remnawave_uuid),
            subscriptionUrl=new_sub_url,
        )
        return httpx.Response(200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.post(
        f'/api/clients/{client.id}/config/rotate',
    )

    assert response.status_code == 200
    assert response.json() == {'config': new_sub_url}


@pytest.mark.asyncio
async def test_create_client_validation_error(api_client):
    response = await api_client.post(
        '/api/clients',
        json={
            'username': 'nm',
            'days': 0,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_remnawave_error(api_client, rw_client, db_session):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={'message': 'error'})

    rw_client._client._transport = httpx.MockTransport(handler)

    response = await api_client.post(
        '/api/clients',
        json={
            'username': 'test_user',
            'days': 30,
        },
    )

    assert response.status_code == 502

    data = response.json()

    assert data.get('type') == 'remnawave_api_error'

    await check_operation(
        db_session,
        action=OperationAction.CREATE_CLIENT,
        result=OperationResult.FAIL,
    )
