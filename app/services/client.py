import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Client
from app.db.models.enums import ClientStatus, OperationAction, OperationResult
from app.domain import OperationCreate
from app.integrations.remnawave import RemnaWaveClient
from app.integrations.remnawave.exceptions import RemnaWaveError
from app.repositories import ClientRepository, OperationRepository


class ClientNotFoundError(Exception):
    pass


class ClientService:
    def __init__(self, session: AsyncSession, rw_client: RemnaWaveClient) -> None:
        self.session = session
        self.client_repo = ClientRepository(session)
        self.operation_repo = OperationRepository(session)
        self.rw_client = rw_client

    async def _get_client_or_raise(self, client_id: uuid.UUID) -> Client:
        client = await self.client_repo.get_by_id(client_id)
        if not client:
            raise ClientNotFoundError(f'Client {client_id} not found')
        return client

    async def _change_client_status(
        self,
        client: Client,
        *,
        status: ClientStatus,
        action: OperationAction,
    ) -> None:
        result = OperationResult.FAIL
        try:
            if status is ClientStatus.ACTIVE:
                await self.rw_client.enable_user(user_uuid=client.remnawave_uuid)
            else:
                await self.rw_client.disable_user(user_uuid=client.remnawave_uuid)

            await self.client_repo.update_status(client, status)

            result = OperationResult.SUCCESS

        except RemnaWaveError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise
        finally:
            await self.operation_repo.create(
                OperationCreate(
                    client_id=client.id,
                    action=action,
                    result=result,
                )
            )
            await self.session.commit()

    async def create_client(self, *, username: str, days: int) -> uuid.UUID:
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        client: Client | None = None
        result = OperationResult.FAIL
        try:
            rw_user = await self.rw_client.create_user(
                username=username,
                expires_at=expires_at,
            )

            client = await self.client_repo.create(
                rw_uuid=rw_user.uuid,
                expires_at=rw_user.expire_at,
            )

            result = OperationResult.SUCCESS
            return client.id

        except RemnaWaveError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise
        finally:
            if client is not None:
                await self.operation_repo.create(
                    OperationCreate(
                        client_id=client.id,
                        action=OperationAction.CREATE_CLIENT,
                        result=result,
                        payload={'username': username},
                    )
                )
                await self.session.commit()

    async def get_client(self, client_id: uuid.UUID) -> Client:
        return await self._get_client_or_raise(client_id)

    async def list_clients(
            self,
            *,
            status: ClientStatus | None = None,
            expired: bool | None = None,
    ) -> Sequence[Client]:
        return await self.client_repo.list(status=status, expired=expired)

    async def extend_subscription(self, *, client_id: uuid.UUID, days: int) -> None:
        client = await self._get_client_or_raise(client_id)
        new_expiration = client.expires_at + timedelta(days=days)

        result = OperationResult.FAIL
        try:
            rw_user = await self.rw_client.update_user(
                user_uuid=client.remnawave_uuid,
                expires_at=new_expiration,
            )

            await self.client_repo.extend_subscription(
                client,
                rw_user.expire_at,
            )

            result = OperationResult.SUCCESS

        except RemnaWaveError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise
        finally:
            await self.operation_repo.create(
                OperationCreate(
                    client_id=client.id,
                    action=OperationAction.EXTEND_SUBSCRIPTION,
                    result=result,
                    payload={
                        'days': days,
                        'new_expiration': new_expiration.isoformat(),
                    },
                )
            )
            await self.session.commit()

    async def block_client(self, *, client_id: uuid.UUID) -> None:
        client = await self._get_client_or_raise(client_id)

        await self._change_client_status(
            client,
            status=ClientStatus.DISABLED,
            action=OperationAction.BLOCK,
        )

    async def unblock_client(self, *, client_id: uuid.UUID) -> None:
        client = await self._get_client_or_raise(client_id)

        await self._change_client_status(
            client,
            status=ClientStatus.ACTIVE,
            action=OperationAction.UNBLOCK,
        )

    async def archive_client(self, *, client_id: uuid.UUID) -> None:
        client = await self._get_client_or_raise(client_id)

        await self._change_client_status(
            client,
            status=ClientStatus.ARCHIVED,
            action=OperationAction.ARCHIVE_CLIENT,
        )

    async def get_config(self, *, client_id: uuid.UUID) -> str:
        client = await self._get_client_or_raise(client_id)

        result = OperationResult.FAIL
        try:
            rw_user = await self.rw_client.get_user(
                user_uuid=client.remnawave_uuid,
            )

            result = OperationResult.SUCCESS
            return rw_user.sub_url
        except RemnaWaveError:
            await self.session.rollback()
            raise
        finally:
            await self.operation_repo.create(
                OperationCreate(
                    client_id=client.id,
                    action=OperationAction.GET_CONFIG,
                    result=result,
                )
            )
            await self.session.commit()

    async def rotate_config(self, *, client_id: uuid.UUID) -> str:
        client = await self._get_client_or_raise(client_id)

        result = OperationResult.FAIL
        try:
            rw_user = await self.rw_client.revoke_subscription(
                user_uuid=client.remnawave_uuid,
            )

            result = OperationResult.SUCCESS
            return rw_user.sub_url

        except RemnaWaveError:
            await self.session.rollback()
            raise
        finally:
            await self.operation_repo.create(
                OperationCreate(
                    client_id=client.id,
                    action=OperationAction.ROTATE_CONFIG,
                    result=result,
                )
            )
            await self.session.commit()
