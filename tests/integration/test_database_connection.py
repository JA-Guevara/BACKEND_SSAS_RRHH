import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.asyncio
async def test_database_connection_executes_select_one() -> None:
    """Comprueba una conexión real usando DATABASE_URL del archivo .env."""
    from ssah.infrastructure.database.session import engine

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1
    except SQLAlchemyError as exc:
        cause = type(exc.__cause__).__name__ if exc.__cause__ else "sin causa interna"
        pytest.fail(f"No se pudo conectar a PostgreSQL ({type(exc).__name__}; causa: {cause})")
    finally:
        await engine.dispose()
