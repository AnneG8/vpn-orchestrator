from collections.abc import Callable

from fastapi import Depends, Request

from app.core import UnitOfWork
from app.db import async_session_factory
from app.integrations.remnawave import RemnaWaveClient
from app.services import ClientService
from app.services.audit import AuditService


def get_rw_client(request: Request) -> RemnaWaveClient:
    return RemnaWaveClient(request.app.state.http_client)


def get_uow_factory() -> Callable[[], UnitOfWork]:
    def factory():
        return UnitOfWork(async_session_factory)
    return factory


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.audit_service


def get_client_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
    rw_client: RemnaWaveClient = Depends(get_rw_client),
    audit_service: AuditService = Depends(get_audit_service),
) -> ClientService:
    return ClientService(
        uow_factory=uow_factory,
        rw_client=rw_client,
        audit_service=audit_service,
    )
