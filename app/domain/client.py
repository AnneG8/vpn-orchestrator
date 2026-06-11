import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.db.models.enums import ClientStatus

from .exceptions import (
    ClientArchivedError,
    InvalidSubscriptionDurationError,
)


@dataclass(slots=True)
class ClientEntity:
    id: uuid.UUID
    remnawave_uuid: uuid.UUID
    status: ClientStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    def _ensure_mutable(self) -> None:
        if self.is_archived:
            raise ClientArchivedError(self.id)

    @property
    def is_active(self) -> bool:
        return self.status == ClientStatus.ACTIVE

    @property
    def is_disabled(self) -> bool:
        return self.status == ClientStatus.DISABLED

    @property
    def is_archived(self) -> bool:
        return self.status == ClientStatus.ARCHIVED

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= datetime.now(timezone.utc)

    def enable(self) -> None:
        self._ensure_mutable()
        self.status = ClientStatus.ACTIVE

    def disable(self) -> None:
        self._ensure_mutable()
        self.status = ClientStatus.DISABLED

    def archive(self) -> None:
        self._ensure_mutable()
        self.status = ClientStatus.ARCHIVED

    def extend_subscription(self, days: int) -> datetime:
        self._ensure_mutable()

        if days <= 0:
            raise InvalidSubscriptionDurationError(days)

        self.expires_at += timedelta(days=days)
        return self.expires_at
