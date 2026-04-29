import copy
import json
import uuid
from datetime import datetime, timezone

import httpx
import pytest

from app.integrations.remnawave.exceptions import (
    RemnaWaveAPIError,
    RemnaWaveConnectionError,
)

TEST_RESPONSE = {
    'response': {
        'activeInternalSquads': [{
            'name': 'Default-Squad',
            'uuid': 'ebc4bef9-a187-45a0-ac96-0e1b0b2b8113'
        }],
        'createdAt': '2026-01-01T00:00:00.000Z',
        'description': None,
        'email': None,
        'expireAt': '2027-01-01T00:00:00.000Z',
        'externalSquadUuid': None,
        'hwidDeviceLimit': None,
        'id': 5,
        'lastTrafficResetAt': None,
        'lastTriggeredThreshold': 0,
        'shortUuid': 'YnAKnx2BsYmzutfM',
        'ssPassword': 'o7qpLaDfwmG3onV4CBmVM8bZamGHmwt5',
        'status': 'ACTIVE',
        'subRevokedAt': None,
        'subscriptionUrl': 'https://test/sub/default_test_url',
        'tag': None,
        'telegramId': None,
        'trafficLimitBytes': 0,
        'trafficLimitStrategy': 'NO_RESET',
        'trojanPassword': '9Dwwa70GNae9k7X8-EVf9gfbV1Y6-adL',
        'updatedAt': '2026-01-01T00:00:00.000Z',
        'userTraffic': {
            'firstConnectedAt': None,
            'lastConnectedNodeUuid': None,
            'lifetimeUsedTrafficBytes': 0,
            'onlineAt': None,
            'usedTrafficBytes': 0
        },
        'username': 'default_test_user',
        'uuid': '36292ccd-7c44-41ce-8f7b-0527fef39e06',
        'vlessUuid': '3452cbe5-4c94-49ee-9b90-2ae450b4d0f0'
    }
}

DEFAULT_SQUAD = 'ebc4bef9-a187-45a0-ac96-0e1b0b2b8113'
SUB_URL = 'https://test/sub/default_test_url'


def build_response(**overrides) -> dict:
    data = copy.deepcopy(TEST_RESPONSE)

    data['response'].update(overrides)

    return data


@pytest.mark.asyncio
async def test_create_user(rw_client):
    user_uuid = uuid.uuid4()
    username = 'test_user'
    expire_at = datetime(2027, 1, 1, tzinfo=timezone.utc)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == 'POST'
        assert request.url.path == '/api/users'

        body = json.loads(request.content)
        assert body['username'] == username
        assert body['status'] == 'ACTIVE'
        assert body['expireAt'] == expire_at.isoformat().replace('+00:00', 'Z')
        assert body['activeInternalSquads'] == [DEFAULT_SQUAD]

        response_json = build_response(
            uuid=str(user_uuid),
            username=body['username'],
            status=body['status'],
            expireAt=expire_at.isoformat(),
        )
        return httpx.Response(status_code=201, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await rw_client.create_user(
        username=username,
        expires_at=expire_at,
    )

    assert result.uuid == user_uuid
    assert result.username == username
    assert result.status.value == 'ACTIVE'
    assert result.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert result.expire_at == expire_at
    assert result.sub_url == SUB_URL


@pytest.mark.asyncio
async def test_get_user(rw_client):
    user_uuid = uuid.uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == 'GET'
        assert request.url.path == f'/api/users/{user_uuid}'

        response_json = build_response(uuid=str(user_uuid))
        return httpx.Response(status_code=200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await rw_client.get_user(user_uuid=user_uuid)

    assert result.uuid == user_uuid
    assert result.username == 'default_test_user'
    assert result.status.value == 'ACTIVE'
    assert result.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert result.expire_at == datetime(2027, 1, 1, tzinfo=timezone.utc)
    assert result.sub_url == SUB_URL


@pytest.mark.asyncio
async def test_update_user(rw_client):
    user_uuid = uuid.uuid4()
    new_expire_at = datetime(2028, 1, 1, tzinfo=timezone.utc)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == 'PATCH'
        assert request.url.path == '/api/users'

        body = json.loads(request.content)
        assert body['uuid'] == str(user_uuid)
        assert body['expireAt'] == new_expire_at.isoformat().replace('+00:00', 'Z')

        response_json = build_response(
            uuid=str(user_uuid),
            expireAt=new_expire_at.isoformat(),
        )
        return httpx.Response(status_code=200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await rw_client.update_user(
        user_uuid=user_uuid,
        expires_at=new_expire_at,
    )

    assert result.uuid == user_uuid
    assert result.username == 'default_test_user'
    assert result.status.value == 'ACTIVE'
    assert result.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert result.expire_at == new_expire_at
    assert result.sub_url == SUB_URL


@pytest.mark.asyncio
async def test_revoke_subscription(rw_client):
    user_uuid = uuid.uuid4()
    new_sub_url = 'https://test/sub/new_test_url'

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == 'POST'
        assert request.url.path == f'/api/users/{user_uuid}/actions/revoke'
        assert json.loads(request.content)['revokeOnlyPasswords'] is False

        response_json = build_response(
            uuid=str(user_uuid),
            subscriptionUrl=new_sub_url,
        )
        return httpx.Response(status_code=200, json=response_json)

    rw_client._client._transport = httpx.MockTransport(handler)

    result = await rw_client.revoke_subscription(user_uuid=user_uuid)

    assert result.uuid == user_uuid
    assert result.username == 'default_test_user'
    assert result.sub_url == new_sub_url


@pytest.mark.asyncio
async def test_connection_error(rw_client):
    def handler(request: httpx.Request):
        raise httpx.ConnectError('error')

    rw_client._client._transport = httpx.MockTransport(handler)

    with pytest.raises(RemnaWaveConnectionError):
        await rw_client.get_user(user_uuid=uuid.uuid4())


@pytest.mark.asyncio
async def test_http_error(rw_client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=400, text='Bad Request')

    rw_client._client._transport = httpx.MockTransport(handler)

    with pytest.raises(RemnaWaveAPIError):
        await rw_client.get_user(user_uuid=uuid.uuid4())
