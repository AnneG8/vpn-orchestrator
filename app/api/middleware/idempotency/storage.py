from __future__ import annotations

import redis.asyncio as redis

from .models import (
    CachedResponse,
    IdempotencyRecord,
    IdempotencyStatus,
)


class IdempotencyStorage:
    def __init__(
            self,
            redis_client: redis.Redis,
            *,
            lock_ttl: int,
            cache_ttl: int,
    ) -> None:
        self._redis = redis_client
        self._lock_ttl = lock_ttl
        self._cache_ttl = cache_ttl

    @staticmethod
    def _key(key: str) -> str:
        return f'idempotency:{key}'

    async def acquire(self, key: str, fingerprint: str) -> bool:
        payload = IdempotencyRecord(
            status=IdempotencyStatus.PROCESSING,
            fingerprint=fingerprint,
        )
        result = await self._redis.set(
            self._key(key),
            payload.model_dump_json(),
            ex=self._lock_ttl,
            nx=True,
        )
        return result is True

    async def get(self, key: str) -> IdempotencyRecord | None:
        data = await self._redis.get(self._key(key))
        if data is None:
            return None
        return IdempotencyRecord.model_validate_json(data)

    async def save_response(
            self,
            key: str,
            fingerprint: str,
            response: CachedResponse,
    ) -> None:
        payload = IdempotencyRecord(
            status=IdempotencyStatus.COMPLETED,
            fingerprint=fingerprint,
            response=response,
        )

        await self._redis.set(
            self._key(key),
            payload.model_dump_json(),
            ex=self._cache_ttl,
        )

    async def clear(self, key: str) -> None:
        await self._redis.delete(self._key(key))
