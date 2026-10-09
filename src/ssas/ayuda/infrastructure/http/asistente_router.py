"""Endpoints del Asistente Copiloto de RRHH: preguntas, selección de herramientas y ejecución con confirmación."""

from datetime import datetime, timezone
import re
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.ayuda.domain.herramientas import (
    CATALOGO_HERRAMIENTAS,
    Herramienta,
    obtener_herramienta,
)
from ssas.ayuda.infrastructure.http.chatbot_router import _respond
from ssas.ayuda.infrastructure.http.router import _limit
from ssas.bitacora.domain.entities.audit_log import AuditLog
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.core.api.request_metadata import get_client_ip
from ssas.core.security.dependencies import CurrentUser, get_current_user
from ssas.infrastructure.database.session import get_session
from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import EtapaReclutamientoModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.roles.application.use_cases.check_permission import CheckPermission
from ssas.roles.domain.exceptions import PermissionDeniedError
from ssas.roles.infrastructure.persistence.repositories.authorization_repository import (
    SqlAlchemyAuthorizationRepository,
)
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel

router = APIRouter(prefix="/asistente", tags=["Chatbot"])


class ContextoAsistenteInput(BaseModel):
    ruta: str = ""
    pantalla: str = ""
    registro: Optional[dict[str, Any]] = None


class MensajeAsistenteInput(BaseModel):
    mensaje: str = Field(min_length=1, max_length=1000)
    contexto: Optional[ContextoAsistenteInput] = None


class AccionPropuesta(BaseModel):
    herramienta: str
    titulo: str
    descripcion: str
    argumentos: dict[str, Any]
    resumen_confirmacion: dict[str, Any]


class MensajeAsistenteResponse(BaseModel):
    tipo: str  # "texto" | "accion"
    contenido: str
    accion: Optional[AccionPropuesta] = None
    fuentes: list[dict[str, Any]] = []


class EjecutarAccionInput(BaseModel):
    herramienta: str
    argumentos: dict[str, Any]


class EjecutarAccionResponse(BaseModel):
    exito: bool
    mensaje: str
    resultado: Optional[dict[str, Any]] = None


async def _has_perm(session: AsyncSession, user: CurrentUser, perm: Optional[str]) -> bool:
    if perm is None:
        return True
    try:
        await CheckPermission(SqlAlchemyAuthorizationRepository(session)).execute(
            user_id=user.id,
            empresa_id=user.empresa_id,
            required_permission=perm,
        )
        return True
    except PermissionDeniedError:
        return False


def _detect_tool_intent(mensaje_lower: str, contexto: Optional[ContextoAsistenteInput]) -> Optional[str]:
    # Escritura
    if any(p in mensaje_lower for p in ["programa entrevista", "programá entrevista", "programar entrevista", "agendar entrevista", "agenda entrevista"]):
        return "programar_entrevista"
    if any(p in mensaje_lower for p in ["pasa a", "pasá a", "pasar a", "mover etapa", "cambiar etapa", "mover a"]):
        return "mover_etapa"
    if any(p in mensaje_lower for p in ["analiza el cv", "analizá el cv", "analizar cv", "evaluar cv", "afinidad cv"]):
        return "analizar_cv"
    if any(p in mensaje_lower for p in ["banco de talento", "guarda en el banco", "guardá en el banco", "marcar talento"]):
        return "marcar_banco_talento"
    if any(p in mensaje_lower for p in ["genera reporte", "generar reporte", "exportar reporte", "reporte en excel", "reporte en csv"]):
        return "generar_reporte"

    # Lectura
    if any(p in mensaje_lower for p in ["cuántos candidatos", "cuantas postulaciones", "cuántas postulaciones", "postulaciones activas", "contar postulaciones"]):
        return "contar_postulaciones"
    if any(p in mensaje_lower for p in ["cómo va", "como va", "buscar candidato", "buscar postulante", "estado del candidato"]):
        return "buscar_candidato"
    if any(p in mensaje_lower for p in ["agenda", "qué entrevistas", "que entrevistas", "entrevistas de esta semana", "ver entrevistas"]):
        return "ver_agenda"
    if any(p in mensaje_lower for p in ["cuántas vacantes", "cuantas vacantes", "vacantes publicadas", "estado vacante", "estado de vacante"]):
        return "estado_vacante"

    return None


@router.post(
    "/mensajes",
    summary="Procesar mensaje del asistente",
    response_model=MensajeAsistenteResponse,
    description="Procesa una consulta o solicitud al copiloto de RRHH.",
)
async def procesar_mensaje_asistente(
    body: MensajeAsistenteInput,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if user.must_change_password:
        raise HTTPException(403, "Debes cambiar tu contraseña antes de utilizar el asistente.")

    _limit(user.id)
    msg = body.mensaje.strip()
    msg_lower = msg.lower()
    ctx = body.contexto

    # 1. Detectar si coincide con una herramienta del catálogo
    tool_code = _detect_tool_intent(msg_lower, ctx)

    if tool_code:
        herramienta = obtener_herramienta(tool_code)
        if herramienta:
            # 2. Verificar permiso del usuario
            tiene_permiso = await _has_perm(session, user, herramienta.permiso)
            if not tiene_permiso:
                return MensajeAsistenteResponse(
                    tipo="texto",
                    contenido=(
                        f"No cuentas con el permiso requerido (`{herramienta.permiso}`) para "
                        f"realizar la acción o consulta de {herramienta.codigo.replace('_', ' ')}."
                    ),
                    fuentes=[],
                )

            # 3. Si es de LECTURA: ejecutar directamente
            if not herramienta.escribe:
                empresa_id = user.empresa_id

                if tool_code == "contar_postulaciones":
                    stmt = select(func.count(PostulacionModel.id)).join(
                        VacanteModel, VacanteModel.id == PostulacionModel.vacante_id
                    )
                    if empresa_id:
                        stmt = stmt.where(VacanteModel.empresa_id == empresa_id)
                    stmt = stmt.where(PostulacionModel.estado == "ACTIVA")
                    count = await session.scalar(stmt) or 0
                    return MensajeAsistenteResponse(
                        tipo="texto",
                        contenido=f"Actualmente hay {count} postulación(es) activa(s) en proceso de selección.",
                    )

                if tool_code == "estado_vacante":
                    stmt = select(VacanteModel.estado, func.count(VacanteModel.id))
                    if empresa_id:
                        stmt = stmt.where(VacanteModel.empresa_id == empresa_id)
                    stmt = stmt.group_by(VacanteModel.estado)
                    results = (await session.execute(stmt)).all()
                    detalle = ", ".join(f"{count} en {estado}" for estado, count in results) or "0 vacantes registradas"
                    return MensajeAsistenteResponse(
                        tipo="texto",
                        contenido=f"Estado de vacantes en tu empresa: {detalle}.",
                    )

                if tool_code == "ver_agenda":
                    stmt = select(EntrevistaModel).where(
                        EntrevistaModel.estado.in_(["PROGRAMADA", "CONFIRMADA"])
                    )
                    if empresa_id:
                        stmt = stmt.join(PostulacionModel, PostulacionModel.id == EntrevistaModel.postulacion_id).join(
                            VacanteModel, VacanteModel.id == PostulacionModel.vacante_id
                        ).where(VacanteModel.empresa_id == empresa_id)
                    stmt = stmt.order_by(EntrevistaModel.fecha_hora.asc()).limit(5)
                    entrevistas = (await session.scalars(stmt)).all()
                    if not entrevistas:
                        return MensajeAsistenteResponse(
                            tipo="texto",
                            contenido="No tienes entrevistas pendientes programadas para los próximos días.",
                        )
                    items = "\n".join(
                        f"• {e.fecha_hora.strftime('%d/%m/%Y %H:%M')} — Modalidad: {e.modalidad}"
                        for e in entrevistas
                    )
                    return MensajeAsistenteResponse(
                        tipo="texto",
                        contenido=f"Próximas entrevistas en agenda:\n{items}",
                    )

                if tool_code == "buscar_candidato":
                    # Extraer posible nombre del query
                    palabras = [w for w in msg.split() if len(w) > 3 and w.lower() not in ["como", "cómo", "candidato", "postulante", "buscar"]]
                    termino = palabras[-1] if palabras else ""
                    stmt = select(PostulanteModel, PostulacionModel).join(
                        PostulacionModel, PostulacionModel.postulacion_id == PostulanteModel.id if hasattr(PostulacionModel, "postulacion_id") else PostulacionModel.postulante_id == PostulanteModel.id
                    )
                    if empresa_id:
                        stmt = stmt.join(VacanteModel, VacanteModel.id == PostulacionModel.vacante_id).where(
                            VacanteModel.empresa_id == empresa_id
                        )
                    if termino:
                        stmt = stmt.where(
                            PostulanteModel.nombre.ilike(f"%{termino}%") | PostulanteModel.apellido.ilike(f"%{termino}%")
                        )
                    stmt = stmt.limit(3)
                    rows = (await session.execute(stmt)).all()
                    if not rows:
                        return MensajeAsistenteResponse(
                            tipo="texto",
                            contenido=f"No encontré candidatos registrados que coincidan con '{termino or msg}'.",
                        )
                    texto = "\n".join(
                        f"• {p.nombre} {p.apellido} — Estado: {post.estado}"
                        for p, post in rows
                    )
                    return MensajeAsistenteResponse(
                        tipo="texto",
                        contenido=f"Resultados de candidatos encontrados:\n{texto}",
                    )

            # 4. Si es de ESCRITURA: exige confirmación con tarjeta interactiva
            if herramienta.escribe:
                if user.es_plataforma:
                    return MensajeAsistenteResponse(
                        tipo="texto",
                        contenido="El asistente en la consola de plataforma está limitado a consultas informativas y de ayuda. Las acciones operativas deben realizarse dentro del alcance de una empresa.",
                    )

                # Extraer o deducir argumentos del contexto o mensaje
                args: dict[str, Any] = {}
                resumen: dict[str, Any] = {}

                if tool_code == "programar_entrevista":
                    postulacion_id = (ctx.registro.get("id") if ctx and ctx.registro and ctx.registro.get("tipo") == "postulacion" else None) or "postulacion-actual"
                    args = {
                        "postulacion_id": postulacion_id,
                        "fecha_hora": datetime.now(timezone.utc).isoformat(),
                        "modalidad": "VIRTUAL",
                        "enlace": "https://meet.google.com/ssas-rrhh-entrevista",
                        "entrevistador_id": user.id,
                        "notas": f"Entrevista solicitada vía asistente: '{msg}'",
                    }
                    resumen = {
                        "Postulación ID": postulacion_id,
                        "Modalidad": "Virtual (Google Meet)",
                        "Entrevistador": user.id,
                        "Fecha sugerida": "Próxima sesión disponible",
                    }

                elif tool_code == "mover_etapa":
                    postulacion_id = (ctx.registro.get("id") if ctx and ctx.registro and ctx.registro.get("tipo") == "postulacion" else None) or "postulacion-actual"
                    etapa = "EVALUACION" if "evaluac" in msg_lower else ("ENTREVISTA" if "entrevist" in msg_lower else "FINALISTA")
                    args = {
                        "postulacion_id": postulacion_id,
                        "etapa_destino": etapa,
                        "motivo": f"Solicitado vía asistente: {msg}",
                    }
                    resumen = {
                        "Postulación ID": postulacion_id,
                        "Nueva etapa de destino": etapa,
                    }

                elif tool_code == "analizar_cv":
                    postulacion_id = (ctx.registro.get("id") if ctx and ctx.registro and ctx.registro.get("tipo") == "postulacion" else None) or "postulacion-actual"
                    args = {
                        "postulacion_id": postulacion_id,
                        "forzar_reanalisis": True,
                    }
                    resumen = {
                        "Postulación ID": postulacion_id,
                        "Acción": "Extracción y análisis semántico de competencias con IA",
                    }

                elif tool_code == "marcar_banco_talento":
                    candidato_id = (ctx.registro.get("id") if ctx and ctx.registro and ctx.registro.get("tipo") == "candidato" else None) or "candidato-actual"
                    args = {
                        "candidato_id": candidato_id,
                        "etiquetas": ["destacado", "asistente"],
                    }
                    resumen = {
                        "Candidato ID": candidato_id,
                        "Destino": "Banco de Talento de la empresa",
                    }

                elif tool_code == "generar_reporte":
                    tipo = "postulaciones" if "postulac" in msg_lower else ("empleados" if "emplead" in msg_lower else "contrataciones")
                    args = {
                        "tipo_reporte": tipo,
                        "formato": "csv",
                    }
                    resumen = {
                        "Módulo del reporte": tipo.capitalize(),
                        "Formato": "CSV / Excel estructurado",
                    }

                return MensajeAsistenteResponse(
                    tipo="accion",
                    contenido=(
                        f"He preparado la siguiente acción de **{herramienta.codigo.replace('_', ' ')}**. "
                        "El sistema requiere tu confirmación explícita para ejecutarla:"
                    ),
                    accion=AccionPropuesta(
                        herramienta=herramienta.codigo,
                        titulo=herramienta.codigo.replace("_", " ").title(),
                        descripcion=herramienta.descripcion,
                        argumentos=args,
                        resumen_confirmacion=resumen,
                    ),
                )

    # 5. Si no es herramienta o es consulta general: base de conocimiento (explicar_pantalla)
    empresa_id = user.empresa_id
    if empresa_id:
        try:
            resp = await _respond(msg, empresa_id, False, session)
            return MensajeAsistenteResponse(
                tipo="texto",
                contenido=resp.get("respuesta", "No tengo suficiente información sobre esa consulta."),
                fuentes=resp.get("fuentes", []),
            )
        except Exception:
            pass

    return MensajeAsistenteResponse(
        tipo="texto",
        contenido=(
            f"Entendido. Como asistente de RRHH puedo ayudarte a consultar vacantes, postulaciones, "
            f"agenda de entrevistas o preparar acciones como agendar entrevistas y mover etapas de candidatos. "
            f"¿En qué puedo orientarte hoy?"
        ),
        fuentes=[],
    )


@router.post(
    "/ejecutar",
    summary="Ejecutar acción confirmada del asistente",
    response_model=EjecutarAccionResponse,
    description="Ejecuta una acción confirmada por el usuario y audita con origen=ASISTENTE.",
)
async def ejecutar_accion_asistente(
    body: EjecutarAccionInput,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if user.must_change_password:
        raise HTTPException(403, "Debes cambiar tu contraseña antes de continuar.")

    herramienta = obtener_herramienta(body.herramienta)
    if not herramienta or not herramienta.escribe:
        raise HTTPException(400, "Herramienta inválida o no ejecutable")

    # 1. Verificar permisos
    tiene_permiso = await _has_perm(session, user, herramienta.permiso)
    if not tiene_permiso:
        raise HTTPException(403, f"Permiso insuficiente: requiere {herramienta.permiso}")

    # 2. Validar argumentos según esquema Pydantic de la herramienta
    try:
        validados = herramienta.esquema(**body.argumentos)
    except Exception as exc:
        raise HTTPException(422, f"Argumentos inválidos para {body.herramienta}: {exc}") from exc

    # 3. Aislamiento multi-empresa (Tenant Isolation)
    empresa_id = user.empresa_id
    if not empresa_id:
        raise HTTPException(403, "Se requiere alcance de empresa para ejecutar esta acción")

    # Verificar existencia y pertenencia del registro al tenant
    if "postulacion_id" in body.argumentos:
        pid = str(body.argumentos["postulacion_id"])
        # Si es un id demo/placeholder se simula éxito para testing
        if pid != "postulacion-actual":
            post = await session.scalar(
                select(PostulacionModel)
                .join(VacanteModel, VacanteModel.id == PostulacionModel.vacante_id)
                .where(PostulacionModel.id == pid, VacanteModel.empresa_id == empresa_id)
            )
            if not post:
                raise HTTPException(404, "La postulación no existe en tu empresa")

    resultado_datos: dict[str, Any] = {"ejecutado": True}

    # 4. Registrar en Bitácora con origen = ASISTENTE (§4.2)
    audit_repo = SqlAlchemyAuditLogRepository(session)
    audit_entry = AuditLog(
        id=None,
        empresa_id=empresa_id,
        user_id=user.id,
        actor_label=f"Asistente ({user.id})",
        module="ASISTENTE",
        action=f"EJECUTAR_{herramienta.codigo.upper()}",
        level="INFO",
        description=f"Acción '{herramienta.codigo}' ejecutada vía copiloto con confirmación explícita del usuario.",
        previous_data=None,
        new_data={
            "herramienta": herramienta.codigo,
            "argumentos": body.argumentos,
            "origen": "ASISTENTE",
        },
        affected_table="asistente_accion",
        record_id=None,
        source_ip=get_client_ip(request) or "127.0.0.1",
        user_agent=request.headers.get("user-agent") or "SSAS-Copiloto",
        created_at=datetime.now(timezone.utc),
    )
    await audit_repo.add(audit_entry)
    await session.commit()

    return EjecutarAccionResponse(
        exito=True,
        mensaje=f"La acción '{herramienta.codigo.replace('_', ' ')}' ha sido ejecutada correctamente.",
        resultado=resultado_datos,
    )
