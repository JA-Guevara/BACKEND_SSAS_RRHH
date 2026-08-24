def test_database_url_uses_async_psycopg_driver() -> None:
    """Comprueba la configuración que la aplicación usará realmente."""
    from ssas.config.settings import settings

    assert settings.database_url.startswith("postgresql+psycopg://")


def test_standard_postgresql_url_is_adapted(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://test_user:test_password@localhost:5432/test_db",
    )
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")

    from ssas.config.settings import Settings

    configured_settings = Settings(_env_file=None)

    assert configured_settings.database_url == (
        "postgresql+psycopg://test_user:test_password@localhost:5432/test_db"
    )
