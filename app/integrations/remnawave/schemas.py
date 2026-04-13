import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings

from .enums import RWUserStatus

USERNAME_PATTERN = r'^[a-zA-Z0-9_-]+$'


class RWClientCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=36,
        pattern=USERNAME_PATTERN,
    )
    status: RWUserStatus = RWUserStatus.ACTIVE
    expire_at: datetime = Field(alias='expireAt')
    active_internal_squads: list[str] = Field(
        default_factory=lambda: [settings.REMNAWAVE_DEFAULT_SQUAD_UUID],
        alias='activeInternalSquads',
    )

    model_config = ConfigDict(populate_by_name=True)


class RWClientUpdate(BaseModel):
    uuid: uuid.UUID
    expire_at: datetime = Field(alias='expireAt')

    model_config = ConfigDict(populate_by_name=True)


class RWClientResponse(BaseModel):
    uuid: uuid.UUID
    username: str = Field(
        min_length=3,
        max_length=36,
        pattern=USERNAME_PATTERN,
    )
    status: RWUserStatus
    created_at: datetime = Field(alias='createdAt')
    expire_at: datetime = Field(alias='expireAt')
    sub_url: str = Field(alias='subscriptionUrl')

    model_config = ConfigDict(populate_by_name=True)


# class RWClientUpdateRequest(BaseModel):
#     uuid: uuid.UUID
#     expire_at: datetime | None = Field(default=None, alias="expireAt")
#
#     model_config = ConfigDict(populate_by_name=True)
