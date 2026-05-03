import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_operation_service
from app.api.schemas import OperationsListResponse
from app.services.operation import OperationService

router = APIRouter(prefix='/operations', tags=['operations'])


@router.get('', response_model=OperationsListResponse)
async def list_operations(
    client_id: uuid.UUID = Query(None, alias='clientId'),
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: OperationService = Depends(get_operation_service),
):
    operations = await service.list_operations(
        client_id=client_id,
        cursor=cursor,
        limit=limit,
    )

    next_cursor = operations[-1].created_at if operations else None

    return {
        'items': operations,
        'next_cursor': next_cursor,
    }
