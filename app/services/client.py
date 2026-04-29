import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence

from app.core import UnitOfWork
from app.db.models import Client
from app.db.models.enums import ClientStatus, OperationAction
from app.integrations.remnawave import RemnaWaveClient

from .audit import AuditService
from .exceptions import ClientNotFoundError, UnsupportedClientStatusError


class ClientService:
    def __init__(
            self,
            uow_factory: Callable[[], UnitOfWork],
            rw_client: RemnaWaveClient,
            audit_service: AuditService,
    ) -> None:
        self._uow_factory = uow_factory
        self._rw_client = rw_client
        self._audit = audit_service

    async def _get_client_or_raise(
            self,
            client_id: uuid.UUID,
            *,
            uow: UnitOfWork,
    ) -> Client:
        client = await uow.client_repo.get_by_id(client_id)
        if not client:
            raise ClientNotFoundError(client_id)
        return client

    async def _change_client_status(
        self,
        client_id: uuid.UUID,
        *,
        status: ClientStatus,
        action: OperationAction,
    ) -> None:
        try:
            async with self._uow_factory() as uow:
                client = await self._get_client_or_raise(client_id, uow=uow)

                match status:
                    case ClientStatus.ACTIVE:
                        await self._rw_client.enable_user(
                            user_uuid=client.remnawave_uuid
                        )
                    case ClientStatus.DISABLED:
                        await self._rw_client.disable_user(
                            user_uuid=client.remnawave_uuid
                        )

                    case ClientStatus.ARCHIVED:
                        await self._rw_client.disable_user(
                            user_uuid=client.remnawave_uuid
                        )

                    case _:
                        raise UnsupportedClientStatusError(status)

                await uow.client_repo.update_status(client, status)

            await self._audit.success(
                client_id=client_id,
                action=action,
            )

        except Exception as err:
            await self._audit.fail(
                client_id=client_id,
                action=action,
                error=err,
            )
            raise

    async def create_client(self, *, username: str, days: int) -> uuid.UUID:
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        client: Client | None = None
        try:
            async with self._uow_factory() as uow:
                rw_user = await self._rw_client.create_user(
                    username=username,
                    expires_at=expires_at,
                )

                client = await uow.client_repo.create(
                    rw_uuid=rw_user.uuid,
                    expires_at=rw_user.expire_at,
                )

            await self._audit.success(
                client_id=client.id,
                action=OperationAction.CREATE_CLIENT,
                payload={'username': username},
            )

            return client.id

        except Exception as err:
            await self._audit.fail(
                client_id=client.id if client else None,
                action=OperationAction.CREATE_CLIENT,
                payload={'username': username},
                error=err,
            )
            raise

    async def get_client(self, *, client_id: uuid.UUID) -> Client:
        async with self._uow_factory() as uow:
            return await self._get_client_or_raise(client_id, uow=uow)

    async def list_clients(
            self,
            *,
            status: ClientStatus | None = None,
            expired: bool | None = None,
    ) -> Sequence[Client]:
        async with self._uow_factory() as uow:
            return await uow.client_repo.list(status=status, expired=expired)

    async def extend_subscription(self, *, client_id: uuid.UUID, days: int) -> None:
        try:
            async with self._uow_factory() as uow:
                client = await self._get_client_or_raise(client_id, uow=uow)
                new_expiration = client.expires_at + timedelta(days=days)

                rw_user = await self._rw_client.update_user(
                    user_uuid=client.remnawave_uuid,
                    expires_at=new_expiration,
                )

                await uow.client_repo.extend_subscription(
                    client,
                    rw_user.expire_at,
                )

            await self._audit.success(
                client_id=client_id,
                action=OperationAction.EXTEND_SUBSCRIPTION,
                payload={
                    'days': days,
                    'new_expiration': new_expiration.isoformat(),
                },
            )

        except Exception as err:
            await self._audit.fail(
                client_id=client_id,
                action=OperationAction.EXTEND_SUBSCRIPTION,
                payload={'days': days},
                error=err,
            )
            raise

    async def block_client(self, *, client_id: uuid.UUID) -> None:
        await self._change_client_status(
            client_id,
            status=ClientStatus.DISABLED,
            action=OperationAction.BLOCK,
        )

    async def unblock_client(self, *, client_id: uuid.UUID) -> None:
        await self._change_client_status(
            client_id,
            status=ClientStatus.ACTIVE,
            action=OperationAction.UNBLOCK,
        )

    async def archive_client(self, *, client_id: uuid.UUID) -> None:
        await self._change_client_status(
            client_id,
            status=ClientStatus.ARCHIVED,
            action=OperationAction.ARCHIVE_CLIENT,
        )

    async def get_config(self, *, client_id: uuid.UUID) -> str:
        try:
            async with self._uow_factory() as uow:
                client = await self._get_client_or_raise(client_id, uow=uow)

                rw_user = await self._rw_client.get_user(
                    user_uuid=client.remnawave_uuid,
                )

            await self._audit.success(
                client_id=client_id,
                action=OperationAction.GET_CONFIG,
            )

            return rw_user.sub_url
        except Exception as err:
            await self._audit.fail(
                client_id=client_id,
                action=OperationAction.GET_CONFIG,
                error=err,
            )
            raise

    async def rotate_config(self, *, client_id: uuid.UUID) -> str:
        try:
            async with self._uow_factory() as uow:
                client = await self._get_client_or_raise(client_id, uow=uow)

                rw_user = await self._rw_client.revoke_subscription(
                    user_uuid=client.remnawave_uuid,
                )

            await self._audit.success(
                client_id=client_id,
                action=OperationAction.ROTATE_CONFIG,
            )

            return rw_user.sub_url

        except Exception as err:
            await self._audit.fail(
                client_id=client_id,
                action=OperationAction.ROTATE_CONFIG,
                error=err,
            )
            raise
