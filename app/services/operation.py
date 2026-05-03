import uuid
from collections.abc import Callable, Sequence
from datetime import datetime

from app.core import UnitOfWork
from app.db.models import Operation


class OperationService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def list_operations(
            self,
            *,
            client_id: uuid.UUID | None = None,
            cursor: datetime | None = None,
            limit: int = 20,
    ) -> Sequence[Operation]:
        async with self._uow_factory() as uow:
            return await uow.operation_repo.list(
                client_id=client_id,
                cursor=cursor,
                limit=limit,
            )
