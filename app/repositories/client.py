import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import Client
from app.db.models.enums import ClientStatus
from app.domain import ClientEntity
from app.repositories import BaseRepository

from .mapper import ClientMapper


class ClientRepository(BaseRepository[Client]):
    @staticmethod
    def _not_archived() -> ColumnElement[bool]:
        return Client.status != ClientStatus.ARCHIVED

    async def create(
        self,
        *,
        rw_uuid: uuid.UUID,
        expires_at: datetime,
        status: ClientStatus = ClientStatus.ACTIVE,
    ) -> ClientEntity:
        client = Client(
            remnawave_uuid=rw_uuid,
            expires_at=expires_at,
            status=status,
        )
        self.session.add(client)
        await self.session.flush()
        return ClientMapper.to_domain(client)

    async def get_by_id(self, client_id: uuid.UUID) -> ClientEntity | None:
        stmt = select(Client).where(Client.id == client_id, self._not_archived())
        result = await self.session.execute(stmt)

        client = result.scalar_one_or_none()
        if not client:
            return None

        return ClientMapper.to_domain(client)

    async def get_by_rw_uuid(self, rw_uuid: uuid.UUID) -> ClientEntity | None:
        stmt = select(Client).where(
            Client.remnawave_uuid == rw_uuid,
            self._not_archived(),
        )
        result = await self.session.execute(stmt)

        client = result.scalar_one_or_none()
        if not client:
            return None

        return ClientMapper.to_domain(client)

    async def list(
        self,
        *,
        status: ClientStatus | None = None,
        expired: bool | None = None,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> Sequence[ClientEntity]:
        stmt = select(Client).where(self._not_archived())

        if status is not None:
            stmt = stmt.where(Client.status == status)

        if expired is not None:
            now = datetime.now(timezone.utc)
            if expired:
                stmt = stmt.where(Client.expires_at < now)
            else:
                stmt = stmt.where(Client.expires_at >= now)

        if cursor is not None:
            stmt = stmt.where(Client.created_at < cursor)

        stmt = stmt.order_by(Client.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)

        clients = result.scalars().all()
        return [ClientMapper.to_domain(client) for client in clients]

    async def update(self, client_entity: ClientEntity) -> None:
        stmt = select(Client).where(Client.id == client_entity.id)
        result = await self.session.execute(stmt)

        client = result.scalar_one()
        ClientMapper.update_model(client, client_entity)

        await self.session.flush()
