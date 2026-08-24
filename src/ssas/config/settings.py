from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str
    app_algorithm: str = "HS256"
    app_access_token_expire_minutes: int = 15
    app_refresh_token_expire_days: int = 7
    app_password_reset_expire_minutes: int = 30
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/app_db"
    db_echo: bool = False
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_recycle_seconds: int = Field(default=1800, ge=30)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Adapta la URL estándar de PostgreSQL al driver asíncrono de SQLAlchemy."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return value.replace(prefix, "postgresql+psycopg://", 1)
        if value.startswith("postgresql+psycopg://"):
            return value
        raise ValueError(
            "DATABASE_URL debe ser una conexión PostgreSQL y no la URL HTTPS del proyecto"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
