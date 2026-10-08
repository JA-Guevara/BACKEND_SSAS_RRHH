import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from html import escape
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from openpyxl import Workbook
from pydantic import ValidationError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.core.api.openapi import TAG_REPORTES
from ssas.core.api.request_metadata import get_client_ip
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.reportes.application.agregador import ejecutar as ejecutar_agregado
from ssas.reportes.domain.catalogo import CATALOGO, Campo
from ssas.reportes.infrastructure.http.ai_provider import (
    GeminiReportInterpreter,
    ReportInterpretationError,
)
from ssas.reportes.infrastructure.http.schemas import (
    ActualizarReporte,
    CrearReporte,
    EnviarReporteRequest,
    InterpretarReporteRequest,
    InterpretarReporteResponse,
    ReporteConfig,
    ReporteResponse,
    VistaPrevia,
)
from ssas.reportes.infrastructure.http.schemas_agregado import (
    ConsultaAgregada,
    RespuestaAgregada,
)
from ssas.reportes.infrastructure.persistence.models.reporte import (
    ReporteDefinicionModel,
    ReporteEjecucionModel,
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


def _empresa(user: CurrentUser, requested: str | None) -> str:
    target = requested if user.es_plataforma else user.empresa_id
    if not target or (not user.es_plataforma and requested and requested != user.empresa_id):
        raise HTTPException(403, "Selecciona una empresa válida")
    return target


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


def _report_field(source: str, field: str) -> str:
    code = field.strip().lower().replace(" ", "_")
    return FIELD_ALIASES[source].get(code, code)


async def _rows(session: AsyncSession, empresa_id: str, config: ReporteConfig) -> list[dict]:
    columns = _validate(config)
    selected = ", ".join(f"{columns[name]} AS {name}" for name in config.columnas)
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
    order = ", ".join(f"{columns[o.campo]} {o.direccion.upper()}" for o in config.orden)
    sql = f"SELECT {selected} FROM {FROM_SQL[config.fuente]} WHERE {' AND '.join(clauses)}"
    if order: sql += f" ORDER BY {order}"
    sql += " LIMIT 5000"
    result = await session.execute(text(sql), params)
    return [dict(row) for row in result.mappings().all()]


def _serialize(model: ReporteDefinicionModel) -> ReporteResponse:
    return ReporteResponse.model_validate(model, from_attributes=True)


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
):
    """Interpreta texto; no envía filas ni el catálogo al proveedor de IA."""
    _empresa(user, empresa_id)
    if not body.texto.strip():
        raise HTTPException(422, "Escribe una consulta para el reporte")
    try:
        result = await GeminiReportInterpreter(settings).interpret(body.texto.strip())
    except ReportInterpretationError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
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


@router.post("", response_model=ReporteResponse, status_code=201)
async def crear(body: CrearReporte, request: Request, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:crear", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Guarda una definición validada para reutilizar columnas, filtros y orden."""
    _validate(body)
    model = ReporteDefinicionModel(empresa_id=_empresa(user, empresa_id), usuario_id=user.id, **body.model_dump())
    session.add(model); await session.flush(); await session.refresh(model)
    await _audit(session, request, user, model.empresa_id, "CREATE", "Definición de reporte creada", model.id, {"nombre": model.nombre, "fuente": model.fuente})
    return _serialize(model)


@router.patch("/{report_id}", response_model=ReporteResponse)
async def actualizar(report_id: str, body: ActualizarReporte, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:editar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Modifica o desactiva una definición perteneciente al alcance autorizado."""
    model = (await session.execute(select(ReporteDefinicionModel).where(ReporteDefinicionModel.id == report_id, ReporteDefinicionModel.empresa_id == _empresa(user, empresa_id)))).scalar_one_or_none()
    if not model: raise HTTPException(404, "Reporte no encontrado")
    for key, value in body.model_dump(exclude_unset=True).items(): setattr(model, key, value)
    _validate(ReporteConfig(fuente=model.fuente, columnas=model.columnas, filtros=model.filtros, orden=model.orden))
    await session.flush(); await session.refresh(model); return _serialize(model)


@router.post("/vista-previa", response_model=VistaPrevia)
async def vista_previa(body: ReporteConfig, empresa_id: str | None = None, page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100), user: CurrentUser = Depends(require_scoped_permission("reportes:ejecutar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Ejecuta una consulta limitada y devuelve una vista previa paginada."""
    rows = await _rows(session, _empresa(user, empresa_id), body); start = (page - 1) * per_page
    return VistaPrevia(columnas=body.columnas, items=rows[start:start + per_page], total=len(rows), page=page, per_page=per_page)


@router.post("/agregado", response_model=RespuestaAgregada)
async def agregado(body: ConsultaAgregada, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:ejecutar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Ejecuta medidas agrupadas sobre el catálogo; alimenta los gráficos del panel."""
    return await ejecutar_agregado(session, body, _empresa(user, empresa_id))


def _document(config: ReporteConfig, rows: list[dict], formato: str) -> tuple[bytes, str]:
    if formato == "html":
        head = "".join(f"<th>{escape(c)}</th>" for c in config.columnas)
        body = "".join("<tr>" + "".join(f"<td>{escape(str(row.get(c, '')))}</td>" for c in config.columnas) + "</tr>" for row in rows)
        return f"<!doctype html><meta charset='utf-8'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>".encode(), "text/html"
    if formato == "xlsx":
        book = Workbook(); sheet = book.active; sheet.append(config.columnas)
        for row in rows: sheet.append([row.get(c) for c in config.columnas])
        output = BytesIO(); book.save(output)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if formato == "pdf":
        output = BytesIO(); canvas = Canvas(output, pagesize=landscape(A4)); y = 560
        canvas.setFont("Helvetica-Bold", 12); canvas.drawString(30, y, " | ".join(config.columnas)); y -= 20
        canvas.setFont("Helvetica", 8)
        for row in rows:
            if y < 30: canvas.showPage(); y = 560; canvas.setFont("Helvetica", 8)
            canvas.drawString(30, y, " | ".join(str(row.get(c, ""))[:35] for c in config.columnas)); y -= 13
        canvas.save(); return output.getvalue(), "application/pdf"
    raise HTTPException(422, "Formato no permitido")


@router.post("/exportar/{formato}")
async def exportar(formato: str, body: ReporteConfig, request: Request, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:exportar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Genera y descarga el reporte en HTML, Excel o PDF y registra la ejecución."""
    target = _empresa(user, empresa_id); rows = await _rows(session, target, body)
    content, media = _document(body, rows, formato)
    session.add(ReporteEjecucionModel(empresa_id=target, usuario_id=user.id, formato=formato, filtros_aplicados=[f.model_dump() for f in body.filtros], estado="COMPLETADO", cantidad_registros=len(rows), fecha_fin=datetime.now(UTC)))
    await _audit(session, request, user, target, "EXPORT", "Reporte exportado", new_data={"formato": formato, "registros": len(rows)})
    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="reporte.{formato}"'})


@router.post("/enviar", status_code=202)
async def enviar(body: EnviarReporteRequest, request: Request, empresa_id: str | None = None, user: CurrentUser = Depends(require_scoped_permission("reportes:enviar", "platform:reportes:gestionar")), session: AsyncSession = Depends(get_session)):
    """Genera el reporte y lo envía como adjunto mediante la configuración SMTP."""
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise HTTPException(503, "El envío de correo no está configurado")
    config = ReporteConfig(**body.model_dump(exclude={"destinatarios", "formato"})); target = _empresa(user, empresa_id)
    rows = await _rows(session, target, config); content, media = _document(config, rows, body.formato)
    message = EmailMessage(); message["Subject"] = "Reporte SSAH RRHH"; message["From"] = settings.smtp_from_email; message["To"] = ", ".join(body.destinatarios); message.set_content("Se adjunta el reporte solicitado.")
    main, sub = media.split("/", 1); message.add_attachment(content, maintype=main, subtype=sub, filename=f"reporte.{body.formato}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_tls: smtp.starttls()
        if settings.smtp_username: smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)
    session.add(ReporteEjecucionModel(empresa_id=target, usuario_id=user.id, formato=body.formato, filtros_aplicados=[f.model_dump() for f in body.filtros], estado="COMPLETADO", cantidad_registros=len(rows), fecha_fin=datetime.now(UTC)))
    await _audit(session, request, user, target, "SEND", "Reporte enviado por correo", new_data={"formato": body.formato, "destinatarios": len(body.destinatarios)})
    return {"message": "Reporte enviado"}
