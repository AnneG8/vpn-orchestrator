from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base
from app.db.models.enums import OperationAction, OperationResult

if TYPE_CHECKING:
    from .client import Client


class Operation(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('client.id', ondelete='SET NULL'),
        nullable=True,
    )

    action: Mapped[OperationAction] = mapped_column(
        Enum(OperationAction, name='operation_action'),
        nullable=False,
    )

    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    result: Mapped[OperationResult] = mapped_column(
        Enum(OperationResult, name='operation_result'),
        nullable=False,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    client: Mapped[Client | None] = relationship(
        'Client',
        back_populates='operations',
    )
