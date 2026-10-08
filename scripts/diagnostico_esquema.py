"""Compara el esquema físico de una base de datos contra el que espera la cadena
de migraciones consolidada. Solo lee: no modifica nada.

Uso:  python scripts/diagnostico_esquema.py
Lee la cadena de conexión de la variable de entorno DATABASE_URL.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Tabla consolidada base Sprint 1 (75aa6ae191e4)
TABLAS_SPRINT_1 = {
    "empresa",
    "modulo",
    "parametro_legal",
    "permiso",
    "plan_suscripcion",
    "empresa_modulo",
    "etapa_reclutamiento",
    "habilidad",
    "motivo_rechazo",
    "parametro_valor",
    "postulante",
    "rol",
    "suscripcion",
    "usuario",
    "bitacora",
    "departamento",
    "email_verification_token",
    "password_reset_token",
    "refresh_token",
    "rol_permiso",
    "usuario_rol",
    "cargo",
    "vacante",
    "postulacion",
    "vacante_habilidad",
    "postulacion_nota",
}

CONSOLIDATED_REVISION = "75aa6ae191e4"


async def revision_actual(conn) -> str | None:
    try:
        res = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        row = res.fetchone()
        return row[0] if row else None
    except Exception:
        return None


async def tablas_fisicas(conn) -> set[str]:
    stmt = text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    res = await conn.execute(stmt)
    return {row[0] for row in res.fetchall() if row[0] != "alembic_version"}


async def columnas_fisicas(conn, tabla: str) -> set[str]:
    stmt = text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :tabla"
    )
    res = await conn.execute(stmt, {"tabla": tabla})
    return {row[0] for row in res.fetchall()}


def tablas_esperadas() -> set[str]:
    return set(TABLAS_SPRINT_1)


def _normalizar_db_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def main() -> int:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Intentar cargar desde ssas.config.settings
        try:
            from ssas.config.settings import settings
            db_url = settings.database_url
        except Exception:
            print("ERROR: DATABASE_URL no está definida en el entorno.")
            return 1

    engine = create_async_engine(_normalizar_db_url(db_url), echo=False)
    try:
        async with engine.connect() as conn:
            rev = await revision_actual(conn)
            fisicas = await tablas_fisicas(conn)
            esperadas = tablas_esperadas()

            existe_en_repo = rev in {
                "75aa6ae191e4",
                "20260914_0002",
                "20260914_0003",
                "20260914_0004",
                "20260915_0005",
                "20260927_0006",
                "20261002_0007",
                "20261003_0008",
                "20261005_0009",
            }

            faltantes = esperadas - fisicas
            sobrantes = fisicas - esperadas

            print(f"Revisión registrada en alembic_version : {rev or '(ninguna)'}")
            print(f"¿Existe en el repositorio?             : {'SÍ' if existe_en_repo else 'NO'}")
            print(f"Tablas físicas                         : {len(fisicas)}")
            print(f"Tablas esperadas por {CONSOLIDATED_REVISION}      : {len(esperadas)}")
            print(f"Tablas faltantes                       : {', '.join(sorted(faltantes)) if faltantes else '(ninguna)'}")
            print(f"Tablas sobrantes                       : {', '.join(sorted(sobrantes)) if sobrantes else '(ninguna)'}")

            if not faltantes:
                print(f"VEREDICTO: compatible → se puede sellar con 'alembic stamp {CONSOLIDATED_REVISION}'")
                return 0
            else:
                print("VEREDICTO: incompatible → requiere reconstrucción o migración manual")
                return 1
    except Exception as exc:
        print(f"ERROR conectando a la base de datos: {exc}")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
