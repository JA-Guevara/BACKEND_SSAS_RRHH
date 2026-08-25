import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.asyncio
async def test_database_connection_executes_select_one() -> None:
    """Comprueba una conexión real usando DATABASE_URL del archivo .env."""
    from ssas.infrastructure.database.session import engine

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1
    except SQLAlchemyError as exc:
        cause = type(exc.__cause__).__name__ if exc.__cause__ else "sin causa interna"
        pytest.fail(
            f"No se pudo conectar a PostgreSQL ({type(exc).__name__}; causa: {cause})",
            pytrace=False,
        )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_platform_schema_is_applied() -> None:
    from ssas.infrastructure.database.session import engine

    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            tables = await connection.execute(
                text(
                    "SELECT to_regclass('public.administrador_plataforma'), "
                    "to_regclass('public.platform_refresh_token'), "
                    "to_regclass('public.bitacora_plataforma')"
                )
            )
        assert revision == "20260825_0004"
        assert all(tables.one())
    finally:
        await engine.dispose()
