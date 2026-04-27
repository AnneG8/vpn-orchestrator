import uuid
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

    async def find_by_client(
        self,
        client_id: uuid.UUID,
    ) -> Sequence[Operation]:
        stmt = (
            select(Operation)
            .where(Operation.client_id == client_id)
            .order_by(Operation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
