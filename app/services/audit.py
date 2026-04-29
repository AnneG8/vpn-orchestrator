from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.enums import OperationAction, OperationResult
from app.domain import OperationCreate
from app.repositories import OperationRepository


class AuditService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def success(
            self,
            *,
            client_id: UUID | None,
            action: OperationAction,
            payload: dict | None = None,
    ) -> None:
        await self._log(
            OperationCreate(
                client_id=client_id,
                action=action,
                result=OperationResult.SUCCESS,
                payload=payload,
            )
        )

    async def fail(
            self,
            *,
            client_id: UUID | None,
            action: OperationAction,
            error: Exception,
            payload: dict | None = None,
    ) -> None:
        await self._log(
            OperationCreate(
                client_id=client_id,
                action=action,
                result=OperationResult.FAIL,
                payload=payload,
                error=self._format_error(error),
            )
        )

    async def _log(self, operation: OperationCreate) -> None:
        async with self._session_factory() as session:
            repo = OperationRepository(session)
            await repo.create(operation)
            await session.commit()

    def _format_error(self, err: Exception) -> str:
        return f'{err.__class__.__name__}: {str(err)}'
