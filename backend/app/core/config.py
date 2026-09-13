from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "BusNBox AI Backend"
    app_version: str = "0.1.0"

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database (optional / development only)
    database_host: str = "127.0.0.1"
    database_port: int = 3306
    database_name: str = "busnbox"
    database_user: str = "busnbox_user"
    database_password: str = ""

    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle: int = 1800

    # Service-to-service Authentication (optional)
    busnbox_api_key: str | None = None
    busnbox_api_key_header: str = "X-BusNBox-Key"
    request_timeout_seconds: float = 30.0

    # Inventory provider
    inventory_provider: str = "mock"
    inventory_api_base_url: str = "http://127.0.0.1:8000"
    inventory_api_search_path: str = "/api/inventory/search"
    inventory_api_key: str | None = None
    inventory_api_key_header: str = "X-API-Key"
    inventory_api_timeout_seconds: float = 15.0
    inventory_api_connect_timeout_seconds: float = 5.0

    # AI provider
    ai_provider: str = "gemini"

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_timeout_seconds: float = 30.0

    # Ollama fallback
    ollama_base_url: str = "http://192.168.1.4:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 180.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @field_validator("ai_provider", mode="before")
    @classmethod
    def validate_ai_provider(cls, value: object) -> str:
        provider = str(value).strip().lower()

        supported_providers = {
            "gemini",
            "ollama",
        }

        if provider not in supported_providers:
            raise ValueError(
                "AI_PROVIDER must be either "
                "'gemini' or 'ollama'."
            )

        return provider

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def clean_gemini_api_key(
        cls,
        value: object,
    ) -> str | None:
        if value is None:
            return None

        api_key = str(value).strip()

        return api_key or None

    @property
    def database_url(self) -> str:
        encoded_user = quote_plus(self.database_user)
        encoded_password = quote_plus(
            self.database_password,
        )

        return (
            f"mysql+asyncmy://"
            f"{encoded_user}:{encoded_password}"
            f"@{self.database_host}:"
            f"{self.database_port}"
            f"/{self.database_name}"
            f"?charset=utf8mb4"
        )

    @property
    def safe_database_url(self) -> str:
        encoded_user = quote_plus(self.database_user)

        return (
            f"mysql+asyncmy://"
            f"{encoded_user}:***"
            f"@{self.database_host}:"
            f"{self.database_port}"
            f"/{self.database_name}"
            f"?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()