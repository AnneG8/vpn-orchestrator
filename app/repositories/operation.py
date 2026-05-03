import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select

from app.db.models import Operation
from app.domain import OperationCreate
from app.repositories import BaseRepository


class OperationRepository(BaseRepository[Operation]):
    async def create(self, data: OperationCreate) -> Operation:
        operation = Operation(
            client_id=data.client_id,
            action=data.action,
            payload=data.payload,
            result=data.result,
            error=data.error,
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def list(
            self,
            *,
            client_id: uuid.UUID | None = None,
            cursor: datetime | None = None,
            limit: int = 20,
    ) -> Sequence[Operation]:
        stmt = select(Operation)

        if client_id is not None:
            stmt = stmt.where(Operation.client_id == client_id)

        if cursor is not None:
            stmt = stmt.where(Operation.created_at < cursor)

        stmt = stmt.order_by(Operation.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
