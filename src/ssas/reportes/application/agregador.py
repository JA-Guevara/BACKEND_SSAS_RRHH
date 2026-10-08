"""Constructor de consultas agregadas sobre el catálogo.

El SQL nunca se arma con texto del usuario: cada campo pasa por el catálogo, el
filtro de inquilino va primero y la granularidad viaja como parámetro.
"""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.reportes.domain.catalogo import CATALOGO, Campo, Fuente, TipoCampo
from ssas.reportes.infrastructure.http.schemas_agregado import (
    Agregacion,
    ConsultaAgregada,
    RespuestaAgregada,
    SerieAgregada,
)

LIMITE_GRUPOS = 500
STATEMENT_TIMEOUT = "15s"


async def aplicar_statement_timeout(session: AsyncSession) -> None:
    """Ninguna consulta de reporte puede tumbar la base para los demás inquilinos."""
    await session.execute(text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'"))

_GRANULARIDAD_PG = {
    "dia": "day",
    "semana": "week",
    "mes": "month",
    "trimestre": "quarter",
    "anio": "year",
}

_FUNCION_MEDIDA = {
    Agregacion.SUMA: "SUM",
    Agregacion.PROMEDIO: "AVG",
    Agregacion.MINIMO: "MIN",
    Agregacion.MAXIMO: "MAX",
}


def _campo(fuente: Fuente, codigo: str, contexto: str) -> Campo:
    campo = fuente.campos.get(codigo)
    if campo is None:
        raise HTTPException(422, f"{contexto}: campo no permitido '{codigo}'")
    return campo


def _clausulas_filtro(consulta: ConsultaAgregada, fuente: Fuente, params: dict[str, Any]) -> list[str]:
    clauses = [f"{fuente.columna_tenant} = :empresa_id"]
    for index, item in enumerate(consulta.filtros):
        campo = _campo(fuente, item.campo, "Filtro")
        expression = campo.sql
        key = f"f{index}"
        if item.operador == "igual":
            clauses.append(f"{expression} = :{key}")
            params[key] = item.valor
        elif item.operador == "contiene":
            clauses.append(f"CAST({expression} AS TEXT) ILIKE :{key}")
            params[key] = f"%{item.valor}%"
        elif item.operador == "mayor_igual":
            clauses.append(f"{expression} >= :{key}")
            params[key] = item.valor
        elif item.operador == "menor_igual":
            clauses.append(f"{expression} <= :{key}")
            params[key] = item.valor
        elif item.operador == "entre" and isinstance(item.valor, list) and len(item.valor) == 2:
            clauses.append(f"{expression} BETWEEN :{key}a AND :{key}b")
            params[f"{key}a"], params[f"{key}b"] = item.valor
        else:
            raise HTTPException(422, "Valor de filtro inválido")
    return clauses


def _agrupaciones(
    consulta: ConsultaAgregada, fuente: Fuente, params: dict[str, Any]
) -> tuple[list[str], dict[str, str]]:
    select: list[str] = []
    alias_por_campo: dict[str, str] = {}
    for index, codigo in enumerate(consulta.agrupar_por):
        campo = _campo(fuente, codigo, "Agrupación")
        if not campo.agrupable:
            raise HTTPException(422, f"El campo '{codigo}' no se puede agrupar")
        expression = campo.sql
        if campo.tipo == TipoCampo.FECHA:
            if consulta.granularidad is None:
                raise HTTPException(422, f"Agrupar por '{codigo}' exige granularidad")
            key = f"g{index}_gran"
            expression = f"date_trunc(:{key}, {campo.sql})"
            params[key] = _GRANULARIDAD_PG[consulta.granularidad]
        alias = f"g{index}"
        alias_por_campo[codigo] = alias
        select.append(f"{expression} AS {alias}")
    return select, alias_por_campo


def _medidas(
    consulta: ConsultaAgregada, fuente: Fuente
) -> tuple[list[str], list[str], dict[str, str]]:
    select: list[str] = []
    etiquetas: list[str] = []
    alias_por_campo: dict[str, str] = {}
    for index, medida in enumerate(consulta.medidas):
        alias = f"m{index}"
        if medida.agregacion == Agregacion.CONTEO:
            etiqueta = medida.etiqueta or "conteo"
            select.append(f"COUNT(*) AS {alias}")
        else:
            campo = _campo(fuente, medida.campo or "", "Medida")
            etiqueta = medida.etiqueta or f"{medida.agregacion.value}_{medida.campo}"
            if medida.agregacion == Agregacion.CONTEO_DISTINTO:
                select.append(f"COUNT(DISTINCT {campo.sql}) AS {alias}")
            else:
                if not campo.agregable or campo.tipo not in (TipoCampo.NUMERO, TipoCampo.FECHA):
                    raise HTTPException(
                        422, f"El campo '{medida.campo}' no admite {medida.agregacion.value}"
                    )
                select.append(f"{_FUNCION_MEDIDA[medida.agregacion]}({campo.sql}) AS {alias}")
            if medida.campo:
                alias_por_campo[medida.campo] = alias
        etiquetas.append(etiqueta)
    return select, etiquetas, alias_por_campo


def construir_sql(consulta: ConsultaAgregada, empresa_id: str) -> tuple[str, dict[str, Any], int]:
    fuente = CATALOGO.get(consulta.fuente)
    if fuente is None:
        raise HTTPException(422, "Fuente de reporte no permitida")

    params: dict[str, Any] = {"empresa_id": empresa_id}
    group_select, alias_grupo = _agrupaciones(consulta, fuente, params)
    measure_select, _, alias_medida = _medidas(consulta, fuente)

    clauses = _clausulas_filtro(consulta, fuente, params)

    order = []
    for item in consulta.orden:
        alias = alias_grupo.get(item.campo) or alias_medida.get(item.campo)
        if alias is None:
            raise HTTPException(422, f"Campo de orden no permitido '{item.campo}'")
        order.append(f"{alias} {item.direccion.upper()}")

    limite = min(consulta.limite, LIMITE_GRUPOS)
    sql = (
        f"SELECT {', '.join(group_select + measure_select)} "
        f"FROM {fuente.from_sql} WHERE {' AND '.join(clauses)}"
    )
    if group_select:
        sql += f" GROUP BY {', '.join(alias_grupo.values())}"
    if order:
        sql += f" ORDER BY {', '.join(order)}"
    sql += f" LIMIT {limite + 1}"
    return sql, params, limite


async def ejecutar(
    session: AsyncSession, consulta: ConsultaAgregada, empresa_id: str
) -> RespuestaAgregada:
    inicio = perf_counter()
    sql, params, limite = construir_sql(consulta, empresa_id)
    await aplicar_statement_timeout(session)
    result = await session.execute(text(sql), params)
    filas = result.mappings().all()
    truncado = len(filas) > limite
    filas = filas[:limite]

    series = []
    for row in filas:
        claves = {codigo: row[f"g{index}"] for index, codigo in enumerate(consulta.agrupar_por)}
        valores = {etiqueta: row[f"m{index}"] for index, etiqueta in enumerate(_etiquetas(consulta))}
        series.append(SerieAgregada(claves=claves, valores=valores))

    return RespuestaAgregada(
        series=series,
        medidas=_etiquetas(consulta),
        total_grupos=len(series),
        truncado=truncado,
        generado_en=datetime.now(UTC),
        milisegundos=int((perf_counter() - inicio) * 1000),
    )


def _etiquetas(consulta: ConsultaAgregada) -> list[str]:
    etiquetas = []
    for medida in consulta.medidas:
        if medida.agregacion == Agregacion.CONTEO:
            etiquetas.append(medida.etiqueta or "conteo")
        else:
            etiquetas.append(medida.etiqueta or f"{medida.agregacion.value}_{medida.campo}")
    return etiquetas