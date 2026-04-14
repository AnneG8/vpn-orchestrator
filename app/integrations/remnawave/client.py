from datetime import datetime
from typing import Any, Generator
from uuid import UUID

import httpx

from app.core.config import settings

from .exceptions import RemnaWaveAPIError, RemnaWaveConnectionError
from .schemas import RWClientCreate, RWClientResponse, RWClientUpdate


class TokenAuth(httpx.Auth):
    def __init__(self, token) -> None:
        self.token = token

    def auth_flow(
            self,
            request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers['Authorization'] = f'Bearer {self.token}'
        yield request


class RemnaWaveClient:
    def __init__(self) -> None:
        self.base_url = settings.REMNAWAVE_URL
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=TokenAuth(settings.REMNAWAVE_TOKEN),
            timeout=10.0,
        )

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as err:
            raise RemnaWaveConnectionError(str(err)) from err
        except httpx.HTTPStatusError as err:
            raise RemnaWaveAPIError(
                message=err.response.text,
                status_code=err.response.status_code,
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

    async def close(self) -> None:
        await self._client.aclose()
