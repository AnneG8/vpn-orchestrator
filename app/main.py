from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title='VPN Orchestrator', lifespan=lifespan)


@app.get('/health')
async def health(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text('SELECT 1'))
    return {'status': 'ok', 'db': result.scalar()}
