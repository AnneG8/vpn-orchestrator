import uuid
from dataclasses import dataclass

from app.db.models.enums import OperationAction, OperationResult


@dataclass(slots=True)
class OperationCreate:
    action: OperationAction
    result: OperationResult
    client_id: uuid.UUID | None = None
    payload: dict | None = None
    error: str | None = None

    def __post_init__(self):
        if self.result == OperationResult.FAIL and not self.error:
            raise ValueError('Error must be provided for failed operation')
