import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select

from app.db.models import Client
from app.db.models.enums import ClientStatus
from app.repositories import BaseRepository


class ClientRepository(BaseRepository[Client]):
    async def create(
        self,
        *,
        rw_uuid: uuid.UUID,
        expires_at: datetime,
        status: ClientStatus = ClientStatus.ACTIVE,
    ) -> Client:
        client = Client(
            remnawave_uuid=rw_uuid,
            expires_at=expires_at,
            status=status,
        )
        self.session.add(client)
        await self.session.flush()
        return client

    async def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        stmt = select(Client).where(
            Client.id == client_id,
            Client.status != ClientStatus.ARCHIVED,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_rw_uuid(self, rw_uuid: uuid.UUID) -> Client | None:
        stmt = select(Client).where(
            Client.remnawave_uuid == rw_uuid,
            Client.status != ClientStatus.ARCHIVED,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: ClientStatus | None = None,
        expired: bool | None = None,
    ) -> Sequence[Client]:
        stmt = select(Client)

        if status is None:
            stmt = stmt.where(Client.status != ClientStatus.ARCHIVED)
        else:
            stmt = stmt.where(Client.status == status)

        if expired is not None:
            now = datetime.now(timezone.utc)
            if expired:
                stmt = stmt.where(Client.expires_at < now)
            else:
                stmt = stmt.where(Client.expires_at >= now)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self,
        client: Client,
        status: ClientStatus,
    ) -> Client:
        client.status = status
        await self.session.flush()
        return client

    async def extend_subscription(
        self,
        client: Client,
        new_expiration: datetime,
    ) -> Client:
        client.expires_at = new_expiration
        await self.session.flush()
        return client
