from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    IDEMPOTENCY_LOCK_TTL: int
    IDEMPOTENCY_CACHE_TTL: int
    DEBUG: bool = False
    REMNAWAVE_URL: str
    REMNAWAVE_TOKEN: str
    REMNAWAVE_DEFAULT_SQUAD_UUID: str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
