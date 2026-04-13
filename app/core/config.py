from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = ''
    REMNAWAVE_URL: str = ''
    REMNAWAVE_TOKEN: str = ''
    REMNAWAVE_DEFAULT_SQUAD_UUID: str = ''

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
