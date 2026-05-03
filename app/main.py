from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exceptions import register_exception_handlers
from app.api.routers import clients_router
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

    app.state.http_client = http_client
    app.state.audit_service = audit_service

    yield

    await app.state.http_client.aclose()


app = FastAPI(title='VPN Orchestrator', lifespan=lifespan)

register_exception_handlers(app)

app.include_router(clients_router, prefix='/api')


@app.get('/health')
async def health(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text('SELECT 1'))
    return {
        'status': 'ok',
        'db': 'ok' if result.scalar() == 1 else 'error',
    }
