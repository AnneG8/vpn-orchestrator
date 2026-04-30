from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from .exceptions import RemnaWaveAPIError, RemnaWaveConnectionError
from .schemas import RWClientCreate, RWClientResponse, RWClientUpdate


class RemnaWaveClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as err:
            raise RemnaWaveConnectionError(str(err), method=method, url=url) from err
        except httpx.HTTPStatusError as err:
            try:
                response_body = err.response.json()
            except ValueError:
                response_body = err.response.text

            raise RemnaWaveAPIError(
                'RemnaWave API returned error',
                status_code=err.response.status_code,
                method=method,
                url=url,
                response_body=response_body,
            ) from err

    async def create_user(
            self, *, username: str, expires_at: datetime
    ) -> RWClientResponse:
        payload = RWClientCreate(
            username=username,
            expire_at=expires_at,
        ).model_dump(by_alias=True, mode='json')

        data = await self._request('POST', '/api/users', json=payload)
        return RWClientResponse.model_validate(data['response'])

    async def get_user(self, *, user_uuid: UUID) -> RWClientResponse:
        data = await self._request('GET', f'/api/users/{user_uuid}')
        return RWClientResponse.model_validate(data['response'])

    async def disable_user(self, *, user_uuid: UUID) -> None:
        await self._request(
            'POST',
            f'/api/users/{user_uuid}/actions/disable',
        )

    async def enable_user(self, *, user_uuid: UUID) -> None:
        await self._request(
            'POST',
            f'/api/users/{user_uuid}/actions/enable',
        )

    async def update_user(
            self, *, user_uuid: UUID, expires_at: datetime
    ) -> RWClientResponse:
        payload = RWClientUpdate(
            uuid=user_uuid,
            expire_at=expires_at,
        ).model_dump(by_alias=True, mode='json')

        data = await self._request('PATCH', '/api/users', json=payload)
        return RWClientResponse.model_validate(data['response'])

    async def revoke_subscription(self, *, user_uuid: UUID) -> RWClientResponse:
        payload = {'revokeOnlyPasswords': False}

        data = await self._request(
            'POST',
            f'/api/users/{user_uuid}/actions/revoke',
            json=payload,
        )
        return RWClientResponse.model_validate(data['response'])
