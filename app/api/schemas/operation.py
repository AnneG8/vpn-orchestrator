import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.enums import OperationAction, OperationResult


class OperationResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID | None
    action: OperationAction
    result: OperationResult
    created_at: datetime
    payload: dict | None
    error: str | None

    model_config = ConfigDict(from_attributes=True)


class OperationsListResponse(BaseModel):
    items: list[OperationResponse]
    next_cursor: datetime | None
