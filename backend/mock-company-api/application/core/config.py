from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BusNBox Mock Company API"
    app_version: str = "0.1.0"

    host: str = "127.0.0.1"
    port: int = 8001
    debug: bool = True

    database_host: str = "127.0.0.1"
    database_port: int = 3306
    database_name: str = "busnbox"
    database_user: str = "busnbox_user"
    database_password: str

    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle: int = 1800

    mock_company_api_key: str = "busnbox-development-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        encoded_user = quote_plus(self.database_user)
        encoded_password = quote_plus(self.database_password)

        return (
            f"mysql+asyncmy://{encoded_user}:{encoded_password}"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}?charset=utf8mb4"
        )

    @property
    def safe_database_url(self) -> str:
        encoded_user = quote_plus(self.database_user)

        return (
            f"mysql+asyncmy://{encoded_user}:***"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()