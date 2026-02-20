from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title='VPN Orchestrator', lifespan=lifespan)


@app.get('/health')
async def health():
    return {'status': 'ok'}
