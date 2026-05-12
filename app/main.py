from contextlib import asynccontextmanager

import httpx
import redis.asyncio as redis
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exceptions import register_exception_handlers
from app.api.middleware import IdempotencyMiddleware, IdempotencyStorage
from app.api.routers import clients_router, operations_router
from app.core.config import settings
from app.db import async_session_factory, get_async_session
from app.integrations.remnawave.auth import TokenAuth
from app.services.audit import AuditService


@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client = httpx.AsyncClient(
        base_url=settings.REMNAWAVE_URL,
        auth=TokenAuth(settings.REMNAWAVE_TOKEN),
        timeout=10.0,
    )
    audit_service = AuditService(async_session_factory)
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    idempotency_storage = IdempotencyStorage(
        redis_client,
        lock_ttl=settings.IDEMPOTENCY_LOCK_TTL,
        cache_ttl=settings.IDEMPOTENCY_CACHE_TTL,
    )

    app.state.http_client = http_client
    app.state.audit_service = audit_service
    app.state.redis = redis_client
    app.state.idempotency_storage = idempotency_storage

    yield

    await app.state.http_client.aclose()
    await redis_client.close()


app = FastAPI(title='VPN Orchestrator', lifespan=lifespan)

app.add_middleware(IdempotencyMiddleware)

register_exception_handlers(app)

app.include_router(clients_router, prefix='/api')
app.include_router(operations_router, prefix='/api')


@app.get('/health')
async def health(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text('SELECT 1'))
    return {
        'status': 'ok',
        'db': 'ok' if result.scalar() == 1 else 'error',
    }
