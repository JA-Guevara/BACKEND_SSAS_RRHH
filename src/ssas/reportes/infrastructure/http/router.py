import csv
import smtplib
from datetime import UTC, datetime
from decimal import Decimal
from email.message import EmailMessage
from html import escape
from io import BytesIO, StringIO

import anyio
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from openpyxl import Workbook
from openpyxl.styles import Font
from pydantic import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.core.api.openapi import TAG_REPORTES
from ssas.core.api.request_metadata import get_client_ip
from ssas.core.api.tenancy import resolver_empresa as _empresa
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.infrastructure.database.session import get_session
from ssas.reportes.application.agregador import (
    aplicar_statement_timeout,
)
from ssas.reportes.application.agregador import (
    ejecutar as ejecutar_agregado,
)
from ssas.reportes.application.cache import cache_agregados, clave_consulta
from ssas.reportes.application.cuotas import (
    FORMATO_IA,
    cuota_de_empresa,
    exportaciones_de_hoy,
    interpretaciones_ia_de_hoy,
    tarjetas_fijadas_de_usuario,
    verificar_exportaciones_dia,
    verificar_filas,
    verificar_interpretaciones_ia,
    verificar_tarjetas_fijadas,
)
from ssas.reportes.domain.catalogo import CATALOGO, Campo, Sensibilidad, campo_de
from ssas.reportes.infrastructure.http.ai_provider import (
    GeminiReportInterpreter,
    ReportInterpretationError,
)
from ssas.reportes.infrastructure.http.schemas import (
    ActualizarReporte,
    ConteoResponse,
    CrearReporte,
    EjecucionResponse,
    EnviarReporteRequest,
    FiltroReporte,
    InterpretarReporteRequest,
    InterpretarReporteResponse,
    OrdenReporte,
    ReporteConfig,
    ReporteResponse,
    VistaPrevia,
)
from ssas.reportes.infrastructure.http.schemas_agregado import (
    ActualizarWidgetPanel,
    Agregacion,
    ConsultaAgregada,
    CrearWidgetPanel,
    Medida,
    RespuestaAgregada,
    WidgetPanelResponse,
)
from ssas.reportes.infrastructure.persistence.models.reporte import (
    ReporteDefinicionModel,
    ReporteEjecucionModel,
    WidgetPanelModel,
)
from ssas.roles.infrastructure.persistence.repositories.authorization_repository import (
    SqlAlchemyAuthorizationRepository,
)

router = APIRouter(prefix="/reportes", tags=[TAG_REPORTES])

# Los mapas SQL se derivan de la capa semántica: una sola definición del catálogo.
SOURCES = {
    code: {name: campo.sql for name, campo in source.campos.items()}
    for code, source in CATALOGO.items()
}
FROM_SQL = {code: source.from_sql for code, source in CATALOGO.items()}
TENANT_COLUMN = {code: source.columna_tenant for code, source in CATALOGO.items()}
LIMITE_FILAS = 5000
FIELD_ALIASES = {
    "vacantes": {"fecha": "fecha_publicacion", "nombre": "titulo", "cargo": "titulo", "ciudad": "ubicacion"},
    "usuarios": {"nombre": "nombres", "apellido": "apellidos", "usuario": "username", "fecha": "ultimo_acceso"},
    "postulaciones": {"fecha": "fecha_postulacion", "nombre": "postulante", "candidato": "postulante", "cargo": "vacante"},
}


async def _audit(session: AsyncSession, request: Request, user: CurrentUser, empresa_id: str, action: str, description: str, record_id: str | None = None, new_data: dict | None = None) -> None:
    await RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)).execute(
        empresa_id=empresa_id, user_id=user.id, module="REPORTES", action=action,
        description=description, affected_table="reporte_definicion", record_id=record_id,
        new_data=new_data, source_ip=get_client_ip(request), user_agent=request.headers.get("user-agent"),
    )


def _validate(config: ReporteConfig) -> dict[str, str]:
    columns = SOURCES.get(config.fuente)
    if not columns:
        raise HTTPException(422, "Fuente de reporte no permitida")
    referenced = set(config.columnas)
    referenced.update(item.campo for item in config.filtros)
    referenced.update(item.campo for item in config.orden)
    invalid = referenced - columns.keys()
    if invalid:
        raise HTTPException(422, f"Campos no permitidos: {', '.join(sorted(invalid))}")
    return columns


def _campos_usados(config: ReporteConfig) -> set[str]:
    campos = set(config.columnas)
    campos.update(item.campo for item in config.filtros)
    campos.update(item.campo for item in config.orden)
    return campos


async def _permisos(session: AsyncSession, user: CurrentUser) -> set[str]:
    return await SqlAlchemyAuthorizationRepository(session).get_user_permission_codes(
        user.id, user.empresa_id
    )


def _autorizar(config: ReporteConfig, permisos: set[str], es_plataforma: bool) -> dict[str, str]:
    columns = _validate(config)
    if es_plataforma:
        return columns
    prohibidos = [
        name
        for name in _campos_usados(config)
        if (campo := campo_de(config.fuente, name))
        and campo.permiso
        and campo.permiso not in permisos
    ]
    if prohibidos:
        raise HTTPException(
            403, f"No tienes permiso para las columnas: {', '.join(sorted(prohibidos))}"
        )
    return columns


def _columnas_sensibles(config: ReporteConfig) -> list[str]:
    return sorted(
        name
        for name in _campos_usados(config)
        if (campo := campo_de(config.fuente, name))
        and campo.sensibilidad in (Sensibilidad.PERSONAL, Sensibilidad.CONFIDENCIAL)
    )


def _autorizar_agregado(
    consulta: ConsultaAgregada, permisos: set[str], es_plataforma: bool
) -> None:
    if es_plataforma:
        return
    if CATALOGO.get(consulta.fuente) is None:
        raise HTTPException(422, "Fuente de reporte no permitida")
    campos = set(consulta.agrupar_por)
    campos.update(medida.campo for medida in consulta.medidas if medida.campo)
    campos.update(filtro.campo for filtro in consulta.filtros)
    campos.update(orden.campo for orden in consulta.orden)
    prohibidos = [
        name
        for name in campos
        if (campo := campo_de(consulta.fuente, name))
        and campo.permiso
        and campo.permiso not in permisos
    ]
    if prohibidos:
        raise HTTPException(
            403, f"No tienes permiso para las columnas: {', '.join(sorted(prohibidos))}"
        )


def _report_field(source: str, field: str) -> str:
    code = field.strip().lower().replace(" ", "_")
    return FIELD_ALIASES[source].get(code, code)


def _where(config: ReporteConfig, columns: dict[str, str], empresa_id: str) -> tuple[str, dict]:
    clauses = [f"{TENANT_COLUMN[config.fuente]} = :empresa_id"]
    params: dict = {"empresa_id": empresa_id}
    for index, item in enumerate(config.filtros):
        expression = columns[item.campo]
        key = f"v{index}"
        if item.operador == "igual":
            clauses.append(f"{expression} = :{key}"); params[key] = item.valor
        elif item.operador == "contiene":
            clauses.append(f"CAST({expression} AS TEXT) ILIKE :{key}"); params[key] = f"%{item.valor}%"
        elif item.operador == "mayor_igual":
            clauses.append(f"{expression} >= :{key}"); params[key] = item.valor
        elif item.operador == "menor_igual":
            clauses.append(f"{expression} <= :{key}"); params[key] = item.valor
        elif item.operador == "entre" and isinstance(item.valor, list) and len(item.valor) == 2:
            clauses.append(f"{expression} BETWEEN :{key}a AND :{key}b")
            params[f"{key}a"], params[f"{key}b"] = item.valor
        else:
            raise HTTPException(422, "Valor de filtro inválido")
    return " AND ".join(clauses), params


async def _rows_truncado(
    session: AsyncSession, empresa_id: str, config: ReporteConfig, limite: int = LIMITE_FILAS
) -> tuple[list[dict], bool]:
    columns = _validate(config)
    selected = ", ".join(f"{columns[name]} AS {name}" for name in config.columnas)
    where, params = _where(config, columns, empresa_id)
    order = ", ".join(f"{columns[o.campo]} {o.direccion.upper()}" for o in config.orden)
    sql = f"SELECT {selected} FROM {FROM_SQL[config.fuente]} WHERE {where}"
    if order: sql += f" ORDER BY {order}"
    sql += f" LIMIT {limite + 1}"
    await aplicar_statement_timeout(session)
    result = await session.execute(text(sql), params)
    rows = [dict(row) for row in result.mappings().all()]
    truncado = len(rows) > limite
    return rows[:limite], truncado


async def _rows(
    session: AsyncSession, empresa_id: str, config: ReporteConfig, limite: int = LIMITE_FILAS
) -> list[dict]:
    rows, _ = await _rows_truncado(session, empresa_id, config, limite)
    return rows


async def _contar(session: AsyncSession, empresa_id: str, config: ReporteConfig) -> int:
    columns = _validate(config)
    where, params = _where(config, columns, empresa_id)
    sql = f"SELECT count(*) AS total FROM {FROM_SQL[config.fuente]} WHERE {where}"
    await aplicar_statement_timeout(session)
    total = await session.scalar(text(sql), params)
    return int(total or 0)


def _serialize(model: ReporteDefinicionModel) -> ReporteResponse:
    return ReporteResponse.model_validate(model, from_attributes=True)


def _serialize_ejecucion(model: ReporteEjecucionModel) -> EjecucionResponse:
    return EjecucionResponse.model_validate(model, from_attributes=True)


def _error_texto(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:500]


async def _nombre_empresa(session: AsyncSession, empresa_id: str) -> str | None:
    return await session.scalar(
        select(EmpresaModel.razon_social).where(EmpresaModel.id == empresa_id)
    )


def _campo_visible(campo: Campo, permisos: set[str], es_plataforma: bool) -> bool:
    return es_plataforma or campo.permiso is None or campo.permiso in permisos


def _serializar_campo(campo: Campo) -> dict:
    data = {
        "codigo": campo.codigo,
        "etiqueta": campo.etiqueta,
        "tipo": campo.tipo.value,
        "agrupable": campo.agrupable,
        "agregable": campo.agregable,
        "sensibilidad": campo.sensibilidad.value,
    }
    if campo.valores:
        data["valores"] = list(campo.valores)
    return data


def _catalogo_visible(permisos: set[str], es_plataforma: bool) -> list[dict]:
    fuentes = []
    for code, fuente in CATALOGO.items():
        if not es_plataforma and fuente.permiso not in permisos:
            continue
        campos = [c for c in fuente.campos.values() if _campo_visible(c, permisos, es_plataforma)]
        if not campos:
            continue
        fuentes.append({
            "codigo": code,
            "nombre": fuente.etiqueta,
            "etiqueta": fuente.etiqueta,
            "descripcion": fuente.descripcion,
            "columnas": [c.codigo for c in campos],
            "campos": [_serializar_campo(c) for c in campos],
        })
    return fuentes


@router.get("/catalogo")
async def catalogo(user: CurrentUser = Depends(require_scoped_permission("reportes:ver", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Devuelve el catálogo ya filtrado: los campos que el usuario no puede ver no existen para él."""
    permisos = await SqlAlchemyAuthorizationRepository(session).get_user_permission_codes(user.id, user.empresa_id)
    return _catalogo_visible(permisos, user.es_plataforma)


@router.post("/interpretar", response_model=InterpretarReporteResponse)
async def interpretar(
    body: InterpretarReporteRequest,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission(
        "reportes:ejecutar", "platform:reportes:gestionar"
    )),
    session: AsyncSession = Depends(get_session),
):
    """Interpreta texto; no envía filas ni el catálogo al proveedor de IA."""
    target = _empresa(user, empresa_id)
    if not body.texto.strip():
        raise HTTPException(422, "Escribe una consulta para el reporte")
    cuota = await cuota_de_empresa(session, target)
    verificar_interpretaciones_ia(cuota, await interpretaciones_ia_de_hoy(session, target))
    try:
        result = await GeminiReportInterpreter(settings).interpret(body.texto.strip())
    except ReportInterpretationError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    session.add(ReporteEjecucionModel(empresa_id=target, usuario_id=user.id, formato=FORMATO_IA, filtros_aplicados=[], columnas_sensibles=[], estado="COMPLETADO", fecha_fin=datetime.now(UTC)))
    if result.necesita_aclaracion:
        return InterpretarReporteResponse(
            config=None, aclaracion=result.aclaracion or "Aclara qué reporte necesitas"
        )
    source = result.fuente.strip().lower()
    source = {"vacante": "vacantes", "usuario": "usuarios", "postulacion": "postulaciones"}.get(source, source)
    if source not in SOURCES:
        return InterpretarReporteResponse(
            config=None, aclaracion="No pude identificar una fuente de reporte disponible"
        )
    try:
        config = ReporteConfig(
            fuente=source,
            columnas=[_report_field(source, field) for field in result.columnas]
            or list(SOURCES[source])[:5],
            filtros=[{
                **item.model_dump(), "campo": _report_field(source, item.campo)
            } for item in result.filtros],
            orden=[{
                **item.model_dump(), "campo": _report_field(source, item.campo)
            } for item in result.orden],
        )
        _validate(config)
    except (ValidationError, HTTPException):
        return InterpretarReporteResponse(
            config=None,
            aclaracion="No pude relacionar todos los campos con el catálogo. Reformula la consulta",
        )
    return InterpretarReporteResponse(config=config)


@router.get("", response_model=list[ReporteResponse])
async def listar(empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:ver", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Lista las definiciones de reportes guardadas dentro de la empresa autorizada."""
    result = await session.execute(select(ReporteDefinicionModel).where(ReporteDefinicionModel.empresa_id == _empresa(user, empresa_id)).order_by(ReporteDefinicionModel.nombre))
    return [_serialize(item) for item in result.scalars().all()]


@router.get("/ejecuciones", response_model=list[EjecucionResponse])
async def ejecuciones(empresa_id: str | None = None, limite: int = Query(50, ge=1, le=200), user: CurrentUser = Depends(require_scoped_permission("reportes:ver", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Historial de ejecuciones (exportaciones y envíos) con su estado y error."""
    result = await session.execute(select(ReporteEjecucionModel).where(ReporteEjecucionModel.empresa_id == _empresa(user, empresa_id)).order_by(ReporteEjecucionModel.fecha_inicio.desc()).limit(limite))
    return [_serialize_ejecucion(item) for item in result.scalars().all()]


@router.post("", response_model=ReporteResponse, status_code=201)
async def crear(body: CrearReporte, request: Request, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:crear", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Guarda una definición validada para reutilizar columnas, filtros y orden."""
    _autorizar(body, await _permisos(session, user), user.es_plataforma)
    model = ReporteDefinicionModel(empresa_id=_empresa(user, empresa_id), usuario_id=user.id, **body.model_dump())
    session.add(model); await session.flush(); await session.refresh(model)
    await _audit(session, request, user, model.empresa_id, "CREATE", "Definición de reporte creada", model.id, {"nombre": model.nombre, "fuente": model.fuente})
    return _serialize(model)



@router.post("/vista-previa", response_model=VistaPrevia)
async def vista_previa(body: ReporteConfig, empresa_id: str | None = None, page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100), user: CurrentUser = Depends(require_scoped_permission("reportes:ejecutar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Ejecuta una consulta limitada y devuelve una vista previa paginada, avisando si truncó."""
    _autorizar(body, await _permisos(session, user), user.es_plataforma)
    rows, truncado = await _rows_truncado(session, _empresa(user, empresa_id), body); start = (page - 1) * per_page
    return VistaPrevia(columnas=body.columnas, items=rows[start:start + per_page], total=len(rows), page=page, per_page=per_page, truncado=truncado, total_exacto=not truncado)


@router.post("/conteo", response_model=ConteoResponse)
async def conteo(body: ReporteConfig, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:ejecutar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Cuenta las filas que devolvería el reporte antes de exportarlo."""
    _autorizar(body, await _permisos(session, user), user.es_plataforma)
    target = _empresa(user, empresa_id)
    cuota = await cuota_de_empresa(session, target)
    total = await _contar(session, target, body)
    return ConteoResponse(total=total, excede_limite=total > cuota.filas_exportacion, limite_del_plan=cuota.filas_exportacion)


@router.post("/agregado", response_model=RespuestaAgregada)
async def agregado(body: ConsultaAgregada, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:ejecutar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Ejecuta medidas agrupadas sobre el catálogo; alimenta los gráficos del panel."""
    _autorizar_agregado(body, await _permisos(session, user), user.es_plataforma)
    target = _empresa(user, empresa_id)
    clave = clave_consulta(body)
    cacheado = cache_agregados.get(target, clave)
    if cacheado is not None:
        return cacheado
    respuesta = await ejecutar_agregado(session, body, target)
    cache_agregados.set(target, clave, respuesta)
    return respuesta


def _etiquetas_columnas(config: ReporteConfig) -> list[str]:
    etiquetas = []
    for codigo in config.columnas:
        campo = campo_de(config.fuente, codigo)
        etiquetas.append(campo.etiqueta if campo else codigo)
    return etiquetas


def _valor_hoja(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime) and valor.tzinfo is not None:
        return valor.astimezone(UTC).replace(tzinfo=None)
    return valor


def _resumen_filtros(config: ReporteConfig) -> str:
    if not config.filtros:
        return "Sin filtros"
    partes = []
    for filtro in config.filtros:
        campo = campo_de(config.fuente, filtro.campo)
        etiqueta = campo.etiqueta if campo else filtro.campo
        valor = filtro.valor
        if isinstance(valor, list):
            valor = " y ".join(str(parte) for parte in valor)
        partes.append(f"{etiqueta} {filtro.operador.replace('_', ' ')} {valor}")
    return "; ".join(partes)


def _xlsx(config: ReporteConfig, rows: list[dict], empresa: str | None, generado_en: datetime | None) -> bytes:
    book = Workbook()
    hoja = book.active
    hoja.title = "Datos"
    hoja.append(_etiquetas_columnas(config))
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    hoja.freeze_panes = "A2"
    for row in rows:
        hoja.append([_valor_hoja(row.get(codigo)) for codigo in config.columnas])
    if rows:
        hoja.auto_filter.ref = hoja.dimensions
    parametros = book.create_sheet("Parámetros")
    resumen = [
        ("Empresa", empresa or ""),
        ("Fuente", config.fuente),
        ("Columnas", ", ".join(_etiquetas_columnas(config))),
        ("Filtros", _resumen_filtros(config)),
        ("Orden", ", ".join(f"{o.campo} {o.direccion}" for o in config.orden) or "Sin orden"),
        ("Generado en", (generado_en or datetime.now(UTC)).isoformat()),
        ("Registros", len(rows)),
    ]
    for etiqueta, valor in resumen:
        parametros.append([etiqueta, valor])
    parametros.column_dimensions["A"].width = 18
    parametros.column_dimensions["B"].width = 90
    output = BytesIO()
    book.save(output)
    return output.getvalue()


def _csv(config: ReporteConfig, rows: list[dict]) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(_etiquetas_columnas(config))
    for row in rows:
        fila = []
        for col in config.columnas:
            val = row.get(col)
            if val is None:
                fila.append("")
            elif isinstance(val, bool):
                fila.append("Sí" if val else "No")
            elif isinstance(val, (datetime, Decimal)):
                fila.append(str(_valor_hoja(val)))
            else:
                fila.append(str(val))
        writer.writerow(fila)
    return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")


class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        page_w, _ = landscape(A4)
        self.drawString(36, 20, "SSAS RRHH · Módulo de Reportes")
        self.drawRightString(page_w - 36, 20, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def _pdf(
    config: ReporteConfig,
    rows: list[dict],
    empresa: str | None,
    generado_en: datetime | None,
) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    fuente_obj = CATALOGO.get(config.fuente)
    titulo_fuente = fuente_obj.etiqueta if fuente_obj else config.fuente.capitalize()
    elements = []

    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
    )
    meta_style = ParagraphStyle(
        "PdfMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    cell_header_style = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "CellData",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b"),
    )

    fecha_str = (generado_en or datetime.now(UTC)).strftime("%d/%m/%Y %H:%M UTC")
    empresa_str = f"Empresa: {empresa} · " if empresa else ""
    meta_line = f"{empresa_str}Fecha: {fecha_str} · Total registros: {len(rows)}"
    filtros_line = f"Filtros: {_resumen_filtros(config)}"

    elements.append(Paragraph(f"Reporte de {titulo_fuente}", title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(meta_line, meta_style))
    elements.append(Paragraph(filtros_line, meta_style))
    elements.append(Spacer(1, 10))

    headers = [
        Paragraph(escape(etiqueta), cell_header_style)
        for etiqueta in _etiquetas_columnas(config)
    ]
    table_data = [headers]

    for row in rows:
        fila_celdas = []
        for col in config.columnas:
            val = row.get(col)
            if val is None:
                txt = "—"
            elif isinstance(val, bool):
                txt = "Sí" if val else "No"
            elif isinstance(val, (datetime, Decimal)):
                txt = str(_valor_hoja(val))
            else:
                txt = str(val)
            fila_celdas.append(Paragraph(escape(txt), cell_style))
        table_data.append(fila_celdas)

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f8259")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    elements.append(table)
    doc.build(elements, canvasmaker=NumberedCanvas)
    return output.getvalue()


def _document(
    config: ReporteConfig,
    rows: list[dict],
    formato: str,
    *,
    empresa: str | None = None,
    generado_en: datetime | None = None,
) -> tuple[bytes, str]:
    if formato == "csv":
        return _csv(config, rows), "text/csv; charset=utf-8"
    if formato == "xlsx":
        return _xlsx(config, rows, empresa, generado_en), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if formato == "pdf":
        return _pdf(config, rows, empresa, generado_en), "application/pdf"
    if formato == "html":
        head = "".join(f"<th>{escape(c)}</th>" for c in config.columnas)
        body = "".join("<tr>" + "".join(f"<td>{escape(str(row.get(c, '')))}</td>" for c in config.columnas) + "</tr>" for row in rows)
        return f"<!doctype html><meta charset='utf-8'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>".encode(), "text/html"
    raise HTTPException(422, f"Formato '{formato}' no permitido")


@router.post("/exportar/{formato}")
async def exportar(
    formato: str,
    body: ReporteConfig,
    request: Request,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission("reportes:exportar", "platform:reportes:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    """Genera y descarga el reporte en XLSX, CSV o PDF y registra la ejecución."""
    if formato not in ("xlsx", "csv", "pdf"):
        raise HTTPException(
            422,
            f"Formato '{formato}' no permitido. Los formatos soportados son xlsx, csv y pdf.",
        )
    _autorizar(body, await _permisos(session, user), user.es_plataforma)
    target = _empresa(user, empresa_id)
    sensibles = _columnas_sensibles(body)
    cuota = await cuota_de_empresa(session, target)
    verificar_filas(cuota, await _contar(session, target, body))
    verificar_exportaciones_dia(cuota, await exportaciones_de_hoy(session, target))
    empresa = await _nombre_empresa(session, target)
    try:
        rows = await _rows(session, target, body, cuota.filas_exportacion)
        content, media = _document(body, rows, formato, empresa=empresa)
    except Exception as exc:
        session.add(
            ReporteEjecucionModel(
                empresa_id=target,
                usuario_id=user.id,
                formato=formato,
                filtros_aplicados=[f.model_dump() for f in body.filtros],
                columnas_sensibles=sensibles,
                estado="ERROR",
                error=_error_texto(exc),
                fecha_fin=datetime.now(UTC),
            )
        )
        await session.commit()
        raise HTTPException(500, "No se pudo generar el reporte") from exc
    session.add(
        ReporteEjecucionModel(
            empresa_id=target,
            usuario_id=user.id,
            formato=formato,
            filtros_aplicados=[f.model_dump() for f in body.filtros],
            columnas_sensibles=sensibles,
            estado="COMPLETADO",
            cantidad_registros=len(rows),
            fecha_fin=datetime.now(UTC),
        )
    )
    await _audit(
        session,
        request,
        user,
        target,
        "EXPORT",
        "Reporte exportado",
        new_data={"formato": formato, "registros": len(rows), "columnas_sensibles": sensibles},
    )
    return Response(
        content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="reporte.{formato}"'},
    )


def _widgets_por_defecto(permisos: set[str], es_plataforma: bool) -> list[WidgetPanelResponse]:
    ahora = datetime.now(UTC)
    candidatos = [
        WidgetPanelResponse(
            id="default-kpi-postulaciones",
            empresa_id="",
            usuario_id="",
            titulo="Postulaciones",
            tipo="kpi",
            consulta=ConsultaAgregada(
                fuente="postulaciones",
                medidas=[Medida(agregacion=Agregacion.CONTEO, etiqueta="Postulaciones")],
            ),
            posicion=0,
            ancho=1,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-kpi-conversion",
            empresa_id="",
            usuario_id="",
            titulo="Tasa de conversión",
            tipo="kpi",
            consulta=ConsultaAgregada(
                fuente="postulaciones",
                medidas=[Medida(agregacion=Agregacion.CONTEO)],
                agrupar_por=["estado"],
            ),
            posicion=1,
            ancho=1,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-kpi-dias-contratacion",
            empresa_id="",
            usuario_id="",
            titulo="Días para contratar",
            tipo="kpi",
            consulta=ConsultaAgregada(
                fuente="postulaciones",
                medidas=[
                    Medida(
                        agregacion=Agregacion.PROMEDIO,
                        campo="dias_hasta_contratacion",
                        etiqueta="Días",
                    )
                ],
            ),
            posicion=2,
            ancho=1,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-kpi-vacantes",
            empresa_id="",
            usuario_id="",
            titulo="Vacantes activas",
            tipo="kpi",
            consulta=ConsultaAgregada(
                fuente="vacantes",
                medidas=[Medida(agregacion=Agregacion.CONTEO)],
                filtros=[
                    FiltroReporte(campo="estado", operador="igual", valor="PUBLICADA")
                ],
            ),
            posicion=3,
            ancho=1,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-embudo",
            empresa_id="",
            usuario_id="",
            titulo="Embudo de selección",
            tipo="embudo",
            consulta=ConsultaAgregada(
                fuente="postulaciones",
                medidas=[Medida(agregacion=Agregacion.CONTEO)],
                agrupar_por=["etapa"],
                orden=[OrdenReporte(campo="etapa_orden", direccion="asc")],
            ),
            posicion=4,
            ancho=2,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-linea-semanal",
            empresa_id="",
            usuario_id="",
            titulo="Postulaciones por semana",
            tipo="linea",
            consulta=ConsultaAgregada(
                fuente="postulaciones",
                medidas=[Medida(agregacion=Agregacion.CONTEO)],
                agrupar_por=["fecha_postulacion"],
                granularidad="semana",
                limite=26,
            ),
            posicion=5,
            ancho=2,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-vacantes-estado",
            empresa_id="",
            usuario_id="",
            titulo="Vacantes por estado",
            tipo="barra_apilada",
            consulta=ConsultaAgregada(
                fuente="vacantes",
                medidas=[Medida(agregacion=Agregacion.CONTEO)],
                agrupar_por=["estado"],
            ),
            posicion=6,
            ancho=2,
            activo=True,
            fecha_registro=ahora,
        ),
        WidgetPanelResponse(
            id="default-afinidad",
            empresa_id="",
            usuario_id="",
            titulo="Afinidad media por vacante",
            tipo="barra",
            consulta=ConsultaAgregada(
                fuente="analisis_cv",
                medidas=[
                    Medida(
                        agregacion=Agregacion.PROMEDIO,
                        campo="puntaje_afinidad",
                    )
                ],
                agrupar_por=["vacante"],
                orden=[OrdenReporte(campo="puntaje_afinidad", direccion="desc")],
                limite=8,
            ),
            posicion=7,
            ancho=2,
            activo=True,
            fecha_registro=ahora,
        ),
    ]
    visibles = []
    for item in candidatos:
        fuente_obj = CATALOGO.get(item.consulta.fuente)
        if fuente_obj and (es_plataforma or fuente_obj.permiso in permisos):
            visibles.append(item)
    return visibles


def _serialize_widget(item: WidgetPanelModel) -> WidgetPanelResponse:
    return WidgetPanelResponse(
        id=item.id,
        empresa_id=item.empresa_id,
        usuario_id=item.usuario_id,
        titulo=item.titulo,
        tipo=item.tipo,  # type: ignore
        consulta=ConsultaAgregada(**item.consulta),
        posicion=item.posicion,
        ancho=item.ancho,
        activo=item.activo,
        fecha_registro=item.fecha_registro,
    )


@router.get("/panel", response_model=list[WidgetPanelResponse])
async def obtener_panel(
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission("reportes:ver", "platform:reportes:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    """Lista las tarjetas fijadas en el panel del usuario o devuelve las tarjetas predeterminadas."""
    target = _empresa(user, empresa_id)
    permisos = await _permisos(session, user)
    stmt = (
        select(WidgetPanelModel)
        .where(
            WidgetPanelModel.empresa_id == target,
            WidgetPanelModel.usuario_id == user.id,
            WidgetPanelModel.activo.is_(True),
        )
        .order_by(WidgetPanelModel.posicion.asc(), WidgetPanelModel.fecha_registro.asc())
    )
    result = await session.execute(stmt)
    guardados = result.scalars().all()
    if guardados:
        items = []
        for item in guardados:
            fuente_obj = CATALOGO.get(item.consulta.get("fuente"))
            if fuente_obj and (user.es_plataforma or fuente_obj.permiso in permisos):
                items.append(_serialize_widget(item))
        return items
    return _widgets_por_defecto(permisos, user.es_plataforma)


@router.post("/panel", response_model=WidgetPanelResponse, status_code=201)
async def fijar_tarjeta(
    body: CrearWidgetPanel,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission("reportes:crear", "platform:reportes:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    """Fija una consulta agregada como tarjeta en el panel del usuario validando la cuota del plan."""
    target = _empresa(user, empresa_id)
    permisos = await _permisos(session, user)
    _autorizar_agregado(body.consulta, permisos, user.es_plataforma)

    cuota = await cuota_de_empresa(session, target)
    existentes = await tarjetas_fijadas_de_usuario(session, target, user.id)
    verificar_tarjetas_fijadas(cuota, existentes)

    model = WidgetPanelModel(
        empresa_id=target,
        usuario_id=user.id,
        titulo=body.titulo,
        tipo=body.tipo,
        consulta=body.consulta.model_dump(),
        posicion=body.posicion or existentes,
        ancho=body.ancho,
        activo=True,
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return _serialize_widget(model)


@router.patch("/panel/{widget_id}", response_model=WidgetPanelResponse)
async def actualizar_tarjeta(
    widget_id: str,
    body: ActualizarWidgetPanel,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission("reportes:editar", "platform:reportes:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza una tarjeta del panel (título, tipo, ancho, orden o consulta)."""
    target = _empresa(user, empresa_id)
    stmt = select(WidgetPanelModel).where(
        WidgetPanelModel.id == widget_id,
        WidgetPanelModel.empresa_id == target,
    )
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Tarjeta no encontrada")

    permisos = await _permisos(session, user)
    if body.consulta is not None:
        _autorizar_agregado(body.consulta, permisos, user.es_plataforma)
        model.consulta = body.consulta.model_dump()
    if body.titulo is not None:
        model.titulo = body.titulo
    if body.tipo is not None:
        model.tipo = body.tipo
    if body.posicion is not None:
        model.posicion = body.posicion
    if body.ancho is not None:
        model.ancho = body.ancho
    if body.activo is not None:
        model.activo = body.activo

    await session.commit()
    await session.refresh(model)
    return _serialize_widget(model)


@router.delete("/panel/{widget_id}", status_code=204)
async def eliminar_tarjeta(
    widget_id: str,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(require_scoped_permission("reportes:editar", "platform:reportes:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    """Elimina una tarjeta del panel del inquilino."""
    target = _empresa(user, empresa_id)
    stmt = select(WidgetPanelModel).where(
        WidgetPanelModel.id == widget_id,
        WidgetPanelModel.empresa_id == target,
    )
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Tarjeta no encontrada")
    await session.delete(model)
    await session.commit()
    return Response(status_code=204)


@router.patch("/{report_id}", response_model=ReporteResponse)
async def actualizar(report_id: str, body: ActualizarReporte, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:editar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Modifica o desactiva una definición perteneciente al alcance autorizado."""
    model = (await session.execute(select(ReporteDefinicionModel).where(ReporteDefinicionModel.id == report_id, ReporteDefinicionModel.empresa_id == _empresa(user, empresa_id)))).scalar_one_or_none()
    if not model: raise HTTPException(404, "Reporte no encontrado")
    for key, value in body.model_dump(exclude_unset=True).items(): setattr(model, key, value)
    _autorizar(ReporteConfig(fuente=model.fuente, columnas=model.columnas, filtros=model.filtros, orden=model.orden), await _permisos(session, user), user.es_plataforma)
    await session.flush(); await session.refresh(model); return _serialize(model)



def _enviar_correo(message: EmailMessage) -> None:
    """E/S bloqueante de SMTP: se ejecuta fuera del bucle de eventos."""
    with smtplib.SMTP(
        settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
    ) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


@router.post("/enviar", status_code=202)
async def enviar(body: EnviarReporteRequest, request: Request, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:enviar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Genera el reporte y lo envía como adjunto mediante la configuración SMTP."""
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise HTTPException(503, "El envío de correo no está configurado")
    config = ReporteConfig(**body.model_dump(exclude={"destinatarios", "formato"})); target = _empresa(user, empresa_id)
    _autorizar(config, await _permisos(session, user), user.es_plataforma)
    sensibles = _columnas_sensibles(config)
    cuota = await cuota_de_empresa(session, target)
    verificar_filas(cuota, await _contar(session, target, config))
    verificar_exportaciones_dia(cuota, await exportaciones_de_hoy(session, target))
    empresa = await _nombre_empresa(session, target)
    try:
        rows = await _rows(session, target, config, cuota.filas_exportacion); content, media = _document(config, rows, body.formato, empresa=empresa)
        message = EmailMessage(); message["Subject"] = "Reporte SSAH RRHH"; message["From"] = settings.smtp_from_email; message["To"] = ", ".join(body.destinatarios); message.set_content("Se adjunta el reporte solicitado.")
        main, sub = media.split("/", 1); message.add_attachment(content, maintype=main, subtype=sub, filename=f"reporte.{body.formato}")
        await anyio.to_thread.run_sync(_enviar_correo, message)
    except Exception as exc:
        session.add(ReporteEjecucionModel(empresa_id=target, usuario_id=user.id, formato=body.formato, filtros_aplicados=[f.model_dump() for f in body.filtros], columnas_sensibles=sensibles, estado="ERROR", error=_error_texto(exc), fecha_fin=datetime.now(UTC)))
        await session.commit()
        raise HTTPException(500, "No se pudo enviar el reporte") from exc
    session.add(ReporteEjecucionModel(empresa_id=target, usuario_id=user.id, formato=body.formato, filtros_aplicados=[f.model_dump() for f in body.filtros], columnas_sensibles=sensibles, estado="COMPLETADO", cantidad_registros=len(rows), fecha_fin=datetime.now(UTC)))
    await _audit(session, request, user, target, "SEND", "Reporte enviado por correo", new_data={"formato": body.formato, "destinatarios": len(body.destinatarios), "columnas_sensibles": sensibles})
    return {"message": "Reporte enviado"}
