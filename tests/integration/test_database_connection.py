import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
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
async def test_minimal_schema_is_applied() -> None:
    from ssas.infrastructure.database.session import engine

    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            tables = await connection.execute(
                text(
                    "SELECT to_regclass('public.empresa'), "
                    "to_regclass('public.usuario'), "
                    "to_regclass('public.rol'), "
                    "to_regclass('public.permiso'), "
                    "to_regclass('public.bitacora')"
                )
            )
        assert revision == "20260825_0001"
        assert all(tables.one())
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_schema_matches_orm_metadata() -> None:
    """Detecta diferencias reales antes de aceptar una revisión como aplicada."""
    from ssas.infrastructure.database.base import Base, import_all_models
    from ssas.infrastructure.database.session import engine

    import_all_models()

    def collect_differences(sync_connection):
        context = MigrationContext.configure(sync_connection)
        return compare_metadata(context, Base.metadata)

    try:
        async with engine.connect() as connection:
            differences = await connection.run_sync(collect_differences)

        assert not differences, f"Diferencias entre PostgreSQL y el ORM: {differences!r}"
    finally:
        await engine.dispose()


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Pruebas de base real: ejecutar con RUN_DATABASE_TESTS=1",
)
