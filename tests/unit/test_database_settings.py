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


def test_cors_defaults_incluyen_origenes_dev_y_produccion(monkeypatch) -> None:
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")

    from ssas.config.settings import Settings

    configured_settings = Settings(_env_file=None)

    assert "http://localhost:5173" in configured_settings.cors_origins
    assert (
        "https://frontendssasrrhh-production.up.railway.app"
        in configured_settings.cors_origins
    )


def test_cors_origin_regex_cubre_subdominios_railway(monkeypatch) -> None:
    import re

    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")

    from ssas.config.settings import Settings

    configured_settings = Settings(_env_file=None)
    regex = re.compile(configured_settings.cors_origin_regex)

    assert regex.match("https://frontendssasrrhh-production.up.railway.app")
    assert regex.match("https://frontendssasrrhh-preview-1234.up.railway.app")
    assert regex.match("https://backendssasrrhh-production.up.railway.app")
    assert not regex.match("https://portal.example.com")
