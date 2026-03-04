import uuid
from dataclasses import dataclass

from app.db.models.enums import OperationAction, OperationResult


@dataclass(slots=True)
class OperationCreate:
    client_id: uuid.UUID
    action: OperationAction
    result: OperationResult
    payload: dict | None = None
    error: str | None = None
