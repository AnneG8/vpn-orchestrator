import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import USERNAME_PATTERN
from app.db.models.enums import ClientStatus


class CreateClientRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=36,
        pattern=USERNAME_PATTERN,
    )
    days: int = Field(gt=0)


class CreateClientResponse(BaseModel):
    id: uuid.UUID


class ExtendSubRequest(BaseModel):
    days: int = Field(gt=0)


class ClientResponse(BaseModel):
    id: uuid.UUID
    status: ClientStatus
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientsListResponse(BaseModel):
    items: list[ClientResponse]
    next_cursor: datetime | None
