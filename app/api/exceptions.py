from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.domain.exceptions import (
    ClientArchivedError,
    InvalidSubscriptionDurationError,
)
from app.integrations.remnawave.exceptions import (
    RemnaWaveAPIError,
    RemnaWaveConnectionError,
)
from app.services.exceptions import ClientNotFoundError


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ClientNotFoundError)
    async def client_not_found_handler(
        request: Request,
        exc: ClientNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'error': str(exc),
                'type': 'client_not_found',
            },
        )

    @app.exception_handler(RemnaWaveConnectionError)
    async def remnawave_connection_handler(
        request: Request,
        exc: RemnaWaveConnectionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                'error': str(exc),
                'type': 'remnawave_connection_error',
            },
        )

    @app.exception_handler(RemnaWaveAPIError)
    async def remnawave_api_handler(
        request: Request,
        exc: RemnaWaveAPIError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                'error': str(exc),
                'type': 'remnawave_api_error',
                'details': exc.response_body,
            },
        )

    @app.exception_handler(ClientArchivedError)
    async def client_archived_handler(
        request: Request,
        exc: ClientArchivedError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'error': str(exc),
                'type': 'client_not_found',
            },
        )

    @app.exception_handler(InvalidSubscriptionDurationError)
    async def invalid_subscription_duration_handler(
        request: Request,
        exc: InvalidSubscriptionDurationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                'error': str(exc),
                'type': 'invalid_subscription_duration_error',
            },
        )

    @app.exception_handler(Exception)
    async def generic_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': str(exc) if settings.DEBUG else 'Internal server error',
                'type': 'internal_error',
            },
        )
