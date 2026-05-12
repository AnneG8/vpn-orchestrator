from __future__ import annotations

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .models import CachedResponse, IdempotencyStatus
from .utils import build_fingerprint


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in {'POST', 'PATCH'}:
            return await call_next(request)

        key = request.headers.get('Idempotency-Key')
        if key is None:
            return await call_next(request)

        storage = request.app.state.idempotency_storage

        fingerprint = await build_fingerprint(request)

        cached = await storage.get(key)
        if cached is not None:
            if cached.fingerprint != fingerprint:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        'error': 'Idempotency key already used with different payload',
                        'type': 'idempotency_fingerprint_mismatch',
                    },
                )

            if cached.status == IdempotencyStatus.PROCESSING:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        'error': 'Request already in progress',
                        'type': 'idempotency_conflict',
                    },
                )

            if cached.status == IdempotencyStatus.COMPLETED:
                response = cached.response
                headers = dict(response.headers)
                headers['X-Idempotency-Replayed'] = 'true'

                return Response(
                    content=response.body,
                    status_code=response.status_code,
                    headers=headers,
                    media_type=response.media_type,
                )

        acquired = await storage.acquire(key, fingerprint=fingerprint)

        if not acquired:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    'error': 'Idempotency key already used with different payload',
                    'type': 'idempotency_fingerprint_mismatch',
                },
            )

        try:
            response = await call_next(request)
        except Exception:
            await storage.clear(key)
            raise

        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            await storage.clear(key)
            return response

        response_body = b''
        if hasattr(response, 'body_iterator'):
            response_body = b''.join([chunk async for chunk in response.body_iterator])
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        elif response.status_code != status.HTTP_204_NO_CONTENT:
            response_body = response.body

        await storage.save_response(
            key,
            fingerprint=fingerprint,
            response=CachedResponse(
                body=response_body.decode(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            ),
        )

        return response
