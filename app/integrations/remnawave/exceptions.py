class RemnaWaveError(Exception):
    """Базовая ошибка RemnaWave"""
    pass


class RemnaWaveAPIError(RemnaWaveError):
    """Ошибка ответа API"""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class RemnaWaveConnectionError(RemnaWaveError):
    """Ошибка соединения"""
    pass
