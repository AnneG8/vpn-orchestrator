import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_client_service
from app.api.schemas import (
    ClientResponse,
    ClientsListResponse,
    CreateClientRequest,
    CreateClientResponse,
    ExtendSubRequest,
)
from app.db.models.enums import ClientStatus
from app.services import ClientService

router = APIRouter(prefix='/clients', tags=['clients'])


@router.post(
    '',
    response_model=CreateClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    data: CreateClientRequest,
    service: ClientService = Depends(get_client_service),
):
    client_id = await service.create_client(
        username=data.username,
        days=data.days,
    )
    return {'id': client_id}


@router.get('/{client_id}', response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    client = await service.get_client(client_id=client_id)
    return client


@router.get('', response_model=ClientsListResponse)
async def list_clients(
    status: ClientStatus | None = Query(None),
    expired: bool | None = Query(None),
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: ClientService = Depends(get_client_service),
):
    clients = await service.list_clients(
        status=status,
        expired=expired,
        cursor=cursor,
        limit=limit,
    )

    next_cursor = clients[-1].created_at if clients else None

    return {
        'items': clients,
        'next_cursor': next_cursor,
    }


@router.post('/{client_id}/extend', status_code=status.HTTP_204_NO_CONTENT)
async def extend_subscription(
    client_id: uuid.UUID,
    data: ExtendSubRequest,
    service: ClientService = Depends(get_client_service),
):
    await service.extend_subscription(
        client_id=client_id,
        days=data.days,
    )


@router.post('/{client_id}/block', status_code=status.HTTP_204_NO_CONTENT)
async def block_client(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    await service.block_client(client_id=client_id)


@router.post('/{client_id}/unblock', status_code=status.HTTP_204_NO_CONTENT)
async def unblock_client(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    await service.unblock_client(client_id=client_id)


@router.delete('/{client_id}', status_code=status.HTTP_204_NO_CONTENT)
async def archive_client(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    await service.archive_client(client_id=client_id)


@router.get('/{client_id}/config')
async def get_config(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    return {'config': await service.get_config(client_id=client_id)}


@router.post('/{client_id}/config/rotate')
async def rotate_config(
    client_id: uuid.UUID,
    service: ClientService = Depends(get_client_service),
):
    return {'config': await service.rotate_config(client_id=client_id)}
