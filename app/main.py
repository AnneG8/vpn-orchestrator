from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_async_session
from app.integrations.remnawave.auth import TokenAuth


@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client = httpx.AsyncClient(
        base_url=settings.REMNAWAVE_URL,
        auth=TokenAuth(settings.REMNAWAVE_TOKEN),
        timeout=10.0,
    )
    app.state.http_client = http_client

    yield

    await http_client.aclose()


app = FastAPI(title='VPN Orchestrator', lifespan=lifespan)


@app.get('/health')
async def health(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text('SELECT 1'))
    return {'status': 'ok', 'db': result.scalar()}
