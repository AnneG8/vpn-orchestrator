from typing import Any


class RemnaWaveError(Exception):
    """Базовая ошибка RemnaWave"""

    def __init__(self, message: str, *, method: str, url: str) -> None:
        self.message = message
        self.method = method
        self.url = url

        super().__init__(message)

    def __str__(self) -> str:
        return f'[{self.method} {self.url}]: {self.message}'


class RemnaWaveAPIError(RemnaWaveError):
    """Ошибка ответа API"""

    def __init__(
            self,
            message: str,
            *,
            status_code: int,
            method: str,
            url: str,
            response_body: Any | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body

        super().__init__(message, method=method, url=url)

    def __str__(self) -> str:
        return f'[{self.method} {self.url}] {self.status_code}: {self.message}'


class RemnaWaveConnectionError(RemnaWaveError):
    """Ошибка соединения"""
    pass
