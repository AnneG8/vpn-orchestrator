import uuid
from dataclasses import dataclass
from datetime import datetime

from app.db.models.enums import ClientStatus


@dataclass(slots=True)
class RWUser:
    uuid: uuid.UUID
    username: str
    status: ClientStatus
    created_at: datetime
    expires_at: datetime
    updated_at: datetime
    sub_url: str
