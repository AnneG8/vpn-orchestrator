from enum import Enum

from pydantic import BaseModel


class IdempotencyStatus(str, Enum):
    PROCESSING = 'processing'
    COMPLETED = 'completed'


class CachedResponse(BaseModel):
    status_code: int
    body: str
    headers: dict[str, str]
    media_type: str | None


class IdempotencyRecord(BaseModel):
    status: IdempotencyStatus
    fingerprint: str
    response: CachedResponse | None = None
