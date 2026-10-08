"""Cuotas por plan del módulo de reportes.

Los límites viven en un solo lugar. El conteo diario sale de `reporte_ejecucion`
(empresa, usuario y fecha): no hace falta una tabla nueva. Las interpretaciones
con IA también se registran allí con `formato="ia"`, de modo que el mismo
histórico sirve para medir el gasto en Gemini.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, time

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.empresas.infrastructure.persistence.models.suscripcion import (
    PlanSuscripcionModel,
    SuscripcionModel,
)
from ssas.reportes.infrastructure.persistence.models.reporte import ReporteEjecucionModel

FORMATOS_EXPORTACION = ("xlsx", "html", "pdf")
FORMATO_IA = "ia"


@dataclass(frozen=True)
class Cuota:
    """Límites de un plan. `None` en un límite diario significa "sin tope"."""

    etiqueta: str
    filas_exportacion: int
    exportaciones_dia: int | None
    tarjetas_fijadas: int
    interpretaciones_ia_dia: int


CUOTAS: dict[str, Cuota] = {
    "basico": Cuota("Básico", 1_000, 20, 4, 10),
    "profesional": Cuota("Profesional", 10_000, 200, 12, 100),
    "premium": Cuota("Premium", 50_000, None, 24, 500),
}
# El plan de la base puede llamarse "Empresarial"; es el mismo tope que Premium.
ALIAS = {"empresarial": "premium", "gratis": "basico", "free": "basico"}
CUOTA_POR_DEFECTO = CUOTAS["basico"]


def _sin_acentos(texto: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(char)
    )


def normalizar_plan(nombre: str | None) -> str:
    if not nombre:
        return "basico"
    clave = _sin_acentos(nombre).strip().lower()
    return ALIAS.get(clave, clave)


def cuota_de_plan(nombre: str | None) -> Cuota:
    """El plan desconocido cae al más restrictivo: nunca ampliar por accidente."""
    return CUOTAS.get(normalizar_plan(nombre), CUOTA_POR_DEFECTO)


async def cuota_de_empresa(session: AsyncSession, empresa_id: str) -> Cuota:
    nombre = await session.scalar(
        select(PlanSuscripcionModel.nombre)
        .join(SuscripcionModel, SuscripcionModel.plan_id == PlanSuscripcionModel.id)
        .where(
            SuscripcionModel.empresa_id == empresa_id,
            SuscripcionModel.estado == "ACTIVA",
        )
        .order_by(SuscripcionModel.fecha_inicio.desc())
        .limit(1)
    )
    return cuota_de_plan(nombre)


def _inicio_de_hoy() -> datetime:
    ahora = datetime.now(UTC)
    return datetime.combine(ahora.date(), time.min, tzinfo=UTC)


async def _conteo_hoy(
    session: AsyncSession, empresa_id: str, formatos: tuple[str, ...]
) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(ReporteEjecucionModel)
        .where(
            ReporteEjecucionModel.empresa_id == empresa_id,
            ReporteEjecucionModel.fecha_inicio >= _inicio_de_hoy(),
            ReporteEjecucionModel.formato.in_(formatos),
        )
    )
    return int(total or 0)


async def exportaciones_de_hoy(session: AsyncSession, empresa_id: str) -> int:
    return await _conteo_hoy(session, empresa_id, FORMATOS_EXPORTACION)


async def interpretaciones_ia_de_hoy(session: AsyncSession, empresa_id: str) -> int:
    return await _conteo_hoy(session, empresa_id, (FORMATO_IA,))


def verificar_filas(cuota: Cuota, filas: int) -> None:
    if filas > cuota.filas_exportacion:
        raise HTTPException(
            429,
            f"El plan {cuota.etiqueta} permite exportar hasta {cuota.filas_exportacion} "
            f"filas por reporte y este tiene {filas}. Mejora tu plan para exportar más.",
        )


def verificar_exportaciones_dia(cuota: Cuota, hechas: int) -> None:
    if cuota.exportaciones_dia is not None and hechas >= cuota.exportaciones_dia:
        raise HTTPException(
            429,
            f"El plan {cuota.etiqueta} permite {cuota.exportaciones_dia} exportaciones "
            "por día y ya alcanzaste el límite. Mejora tu plan para exportar más.",
        )


def verificar_interpretaciones_ia(cuota: Cuota, hechas: int) -> None:
    if hechas >= cuota.interpretaciones_ia_dia:
        raise HTTPException(
            429,
            f"El plan {cuota.etiqueta} permite {cuota.interpretaciones_ia_dia} "
            "interpretaciones con IA por día y ya alcanzaste el límite. Mejora tu plan "
            "para interpretar más.",
        )