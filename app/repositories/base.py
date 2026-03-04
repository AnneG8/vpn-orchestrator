from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar('ModelT')


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def _flush_and_return(self, instance: ModelT) -> ModelT:
        await self.session.flush()
        return instance
