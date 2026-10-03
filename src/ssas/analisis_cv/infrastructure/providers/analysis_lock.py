import hashlib
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from ssas.analisis_cv.domain.analysis import AnalisisCvError


def lock_key(postulacion_id: str, phase: str) -> int:
    value = f"ssas:analisis_cv:{phase}:{postulacion_id}".encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big", signed=True)


@asynccontextmanager
async def _dedicated_connection(engine: AsyncEngine):
    lock_engine = create_async_engine(engine.url, poolclass=NullPool)
    try:
        async with lock_engine.connect() as connection:
            yield await connection.execution_options(isolation_level="AUTOCOMMIT")
    finally:
        await lock_engine.dispose()


@asynccontextmanager
async def analysis_lock(engine: AsyncEngine, postulacion_id: str, *, max_slots: int = 2):
    running = lock_key(postulacion_id, "running")
    persisting = lock_key(postulacion_id, "persisting")
    async with _dedicated_connection(engine) as connection:
        acquired = False
        probing = False
        slot = None
        try:
            acquired = bool(
                await connection.scalar(
                    text("SELECT pg_try_advisory_lock(:key)"),
                    {"key": running},
                )
            )
            if not acquired:
                raise AnalisisCvError("Ya hay un analisis en curso para esta postulacion", 409)
            # The previous request may have returned but not committed its persistence yet.
            probing = True
            available = bool(
                await connection.scalar(
                    text("SELECT pg_try_advisory_lock(:key)"),
                    {"key": persisting},
                )
            )
            if not available:
                raise AnalisisCvError("El analisis anterior aun se esta guardando", 409)
            await connection.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": persisting},
            )
            probing = False
            for index in range(max_slots):
                key = lock_key(str(index), "global_slot")
                if await connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key}):
                    slot = key
                    break
            if slot is None:
                raise AnalisisCvError("La capacidad de analisis esta ocupada; reintente", 503)
            yield
        finally:
            try:
                if slot is not None:
                    await connection.execute(
                        text("SELECT pg_advisory_unlock(:key)"),
                        {"key": slot},
                    )
                if probing:
                    await connection.execute(
                        text("SELECT pg_advisory_unlock(:key)"),
                        {"key": persisting},
                    )
                await connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": running},
                )
            except BaseException:
                # Invalidate failed connections; NullPool also closes them physically.
                await connection.invalidate()
                raise


async def lock_persistence(session: AsyncSession, postulacion_id: str) -> None:
    available = await session.scalar(
        text("SELECT pg_try_advisory_xact_lock(:key)"),
        {"key": lock_key(postulacion_id, "persisting")},
    )
    if not available:
        raise AnalisisCvError("El analisis anterior aun se esta guardando", 409)
