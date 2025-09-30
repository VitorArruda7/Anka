from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="Anka Investment Dashboard")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = Field(default=60)
    algorithm: str = Field(default="HS256")

    database_url: str = Field(
        default="postgresql+asyncpg://invest:investpw@db/investdb",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    brapi_token: str | None = Field(default=None, alias="BRAPI_TOKEN")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
