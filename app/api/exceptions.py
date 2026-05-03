from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.integrations.remnawave.exceptions import (
    RemnaWaveAPIError,
    RemnaWaveConnectionError,
)
from app.services.exceptions import (
    ClientNotFoundError,
    UnsupportedClientStatusError,
)


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

    @app.exception_handler(UnsupportedClientStatusError)
    async def unsupported_status_handler(
        request: Request,
        exc: UnsupportedClientStatusError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'error': str(exc),
                'type': 'unsupported_status',
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

    @app.exception_handler(Exception)
    async def generic_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                # 'error': 'Internal server error',
                'error': str(exc),
                'type': 'internal_error',
            },
        )
