import asyncio
import hashlib
import os
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.core.api.openapi import TAG_RESPALDOS
from ssas.core.security.dependencies import (
    CurrentUser,
    get_current_user,
    require_platform_permission,
)
from ssas.infrastructure.database.session import get_session
from ssas.respaldos.infrastructure.http.schemas import (
    ActualizarRespaldoProgramacionSchema,
    CrearRespaldoProgramacionSchema,
    CrearRespaldoSchema,
    OperacionRespaldoSchema,
    RespaldoProgramacionSchema,
    RespaldoSchema,
    RestaurarRespaldoSchema,
    VerificarIntegridadResponseSchema,
)
from ssas.respaldos.infrastructure.persistence.models.respaldo import (
    RespaldoModel,
    RespaldoProgramacionModel,
)
from ssas.respaldos.infrastructure.services.jobs import (
    calcular_proxima_ejecucion,
    create_backup_job,
    restore_backup_job,
    storage,
)

router = APIRouter(prefix="/respaldos", tags=[TAG_RESPALDOS])


async def _get_completed(session: AsyncSession, respaldo_id: str) -> RespaldoModel:
    respaldo = await session.get(RespaldoModel, respaldo_id)
    if respaldo is None:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
    if respaldo.estado != "COMPLETADO" or not respaldo.ruta_storage:
        raise HTTPException(status_code=409, detail="El respaldo todavía no está disponible")
    return respaldo


async def _audit(
    session: AsyncSession, respaldo: RespaldoModel, user_id: str, action: str, description: str
) -> None:
    await RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)).execute(
        empresa_id=None,
        module="BACKUP",
        action=action,
        description=description,
        user_id=user_id,
        affected_table="respaldo",
        record_id=respaldo.id,
        new_data={"nombre": respaldo.nombre, "sha256": respaldo.sha256},
    )


@router.get(
    "",
    response_model=list[RespaldoSchema],
    summary="Listar respaldos",
    description="Lista hasta cien respaldos del sistema, ordenados desde el más reciente.",
)
async def list_backups(
    _user: CurrentUser = Depends(require_platform_permission("platform:backup:ver")),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(RespaldoModel).order_by(RespaldoModel.fecha_creacion.desc()).limit(100)
    )
    return result.scalars().all()


@router.post(
    "",
    response_model=OperacionRespaldoSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Crear respaldo completo",
    description="Programa un volcado del esquema público y lo guarda en Storage privado.",
)
async def create_backup(
    request: CrearRespaldoSchema,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:crear")),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(UTC)
    respaldo = RespaldoModel(
        id=str(uuid4()),
        nombre=(request.nombre or f"SSAS RRHH {now:%Y-%m-%d %H:%M UTC}").strip(),
        formato="tar.gz",
        estado="PENDIENTE",
        creado_por_id=user.id,
        fecha_creacion=now,
    )
    session.add(respaldo)
    await session.commit()
    background_tasks.add_task(create_backup_job, respaldo.id)
    return OperacionRespaldoSchema(
        id=respaldo.id, estado=respaldo.estado, mensaje="El respaldo comenzó a generarse"
    )


# -------------------------------------------------------------
# Programaciones de respaldo (S-16 .. S-20)
# -------------------------------------------------------------


@router.get(
    "/programaciones",
    response_model=list[RespaldoProgramacionSchema],
    summary="Listar programaciones de respaldo",
    description="Lista las programaciones automáticas de respaldo configuradas.",
)
async def list_scheduled_policies(
    empresa_id: str | None = None,
    _user: CurrentUser = Depends(require_platform_permission("platform:backup:ver")),
    session: AsyncSession = Depends(get_session),
):
    query = select(RespaldoProgramacionModel).order_by(RespaldoProgramacionModel.fecha_creacion.desc())
    if empresa_id:
        query = query.where(RespaldoProgramacionModel.empresa_id == empresa_id)
    result = await session.execute(query)
    return result.scalars().all()


@router.post(
    "/programaciones",
    response_model=RespaldoProgramacionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear programación de respaldo",
    description="Crea una nueva programación periódica (diaria, semanal o mensual) con política de retención.",
)
async def create_scheduled_policy(
    request: CrearRespaldoProgramacionSchema,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:crear")),
    session: AsyncSession = Depends(get_session),
):
    proxima = calcular_proxima_ejecucion(
        request.frecuencia, request.hora, request.dia_semana, request.dia_mes
    )
    prog = RespaldoProgramacionModel(
        id=str(uuid4()),
        empresa_id=request.empresa_id,
        nombre=request.nombre.strip(),
        frecuencia=request.frecuencia,
        hora=request.hora,
        dia_semana=request.dia_semana,
        dia_mes=request.dia_mes,
        retencion_dias=request.retencion_dias,
        activo=True,
        proxima_ejecucion=proxima,
        creado_por_id=user.id,
    )
    session.add(prog)
    await session.commit()
    await session.refresh(prog)
    return prog


@router.patch(
    "/programaciones/{programacion_id}",
    response_model=RespaldoProgramacionSchema,
    summary="Actualizar programación de respaldo",
    description="Actualiza una programación existente y recalcula su próxima ejecución si cambiaron sus parámetros.",
)
async def update_scheduled_policy(
    programacion_id: str,
    request: ActualizarRespaldoProgramacionSchema,
    _user: CurrentUser = Depends(require_platform_permission("platform:backup:crear")),
    session: AsyncSession = Depends(get_session),
):
    prog = await session.get(RespaldoProgramacionModel, programacion_id)
    if prog is None:
        raise HTTPException(status_code=404, detail="Programación no encontrada")

    if request.nombre is not None:
        prog.nombre = request.nombre.strip()
    if request.activo is not None:
        prog.activo = request.activo
    if request.retencion_dias is not None:
        prog.retencion_dias = request.retencion_dias

    recalcular = False
    if request.frecuencia is not None:
        prog.frecuencia = request.frecuencia
        recalcular = True
    if request.hora is not None:
        prog.hora = request.hora
        recalcular = True
    if request.dia_semana is not None:
        prog.dia_semana = request.dia_semana
        recalcular = True
    if request.dia_mes is not None:
        prog.dia_mes = request.dia_mes
        recalcular = True

    if recalcular:
        prog.proxima_ejecucion = calcular_proxima_ejecucion(
            prog.frecuencia, prog.hora, prog.dia_semana, prog.dia_mes
        )

    await session.commit()
    await session.refresh(prog)
    return prog


@router.delete(
    "/programaciones/{programacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar programación de respaldo",
    description="Elimina una programación de respaldo automático.",
)
async def delete_scheduled_policy(
    programacion_id: str,
    _user: CurrentUser = Depends(require_platform_permission("platform:backup:crear")),
    session: AsyncSession = Depends(get_session),
):
    prog = await session.get(RespaldoProgramacionModel, programacion_id)
    if prog is None:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    await session.delete(prog)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/programaciones/{programacion_id}/ejecutar-ahora",
    response_model=OperacionRespaldoSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar programación de respaldo inmediatamente",
    description="Dispara manualmente la ejecución inmediata de una programación de respaldo.",
)
async def run_scheduled_policy_now(
    programacion_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:crear")),
    session: AsyncSession = Depends(get_session),
):
    prog = await session.get(RespaldoProgramacionModel, programacion_id)
    if prog is None:
        raise HTTPException(status_code=404, detail="Programación no encontrada")

    now = datetime.now(UTC)
    respaldo = RespaldoModel(
        id=str(uuid4()),
        nombre=f"{prog.nombre} (Manual {now:%Y-%m-%d %H:%M UTC})",
        formato="tar.gz",
        estado="PENDIENTE",
        creado_por_id=user.id,
        fecha_creacion=now,
        programacion_id=prog.id,
    )
    session.add(respaldo)
    prog.ultima_ejecucion = now
    await session.commit()
    background_tasks.add_task(create_backup_job, respaldo.id)
    return OperacionRespaldoSchema(
        id=respaldo.id,
        estado=respaldo.estado,
        mensaje="El respaldo programado comenzó a generarse",
    )


@router.post(
    "/programaciones/procesar",
    summary="Procesar programaciones de respaldo vencidas (cron o plataforma)",
    description="Busca todas las programaciones activas cuya próxima ejecución ya venció y encola su generación.",
)
async def process_overdue_scheduled_backups(
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    service_key = request.headers.get("X-Service-Key")
    expected_key = os.getenv("BACKUP_SERVICE_KEY", settings.app_secret_key)
    autorizado = bool(service_key and service_key == expected_key)

    actor_id = "SISTEMA_CRON"
    if not autorizado:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            from fastapi.security import HTTPAuthorizationCredentials
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth[7:])
            try:
                user = await get_current_user(creds)
                if user.es_plataforma:
                    autorizado = True
                    actor_id = user.id
            except Exception:
                pass

    if not autorizado:
        raise HTTPException(status_code=401, detail="No autorizado para procesar respaldos programados")

    now = datetime.now(UTC)
    result = await session.execute(
        select(RespaldoProgramacionModel).where(
            RespaldoProgramacionModel.activo.is_(True),
            RespaldoProgramacionModel.proxima_ejecucion <= now,
        )
    )
    vencidas = result.scalars().all()
    encolados = []

    for prog in vencidas:
        respaldo = RespaldoModel(
            id=str(uuid4()),
            nombre=f"{prog.nombre} ({now:%Y-%m-%d %H:%M UTC})",
            formato="tar.gz",
            estado="PENDIENTE",
            creado_por_id=actor_id if len(actor_id) == 36 else prog.creado_por_id,
            fecha_creacion=now,
            programacion_id=prog.id,
        )
        session.add(respaldo)
        prog.ultima_ejecucion = now
        prog.proxima_ejecucion = calcular_proxima_ejecucion(
            prog.frecuencia, prog.hora, prog.dia_semana, prog.dia_mes, now
        )
        await session.commit()
        background_tasks.add_task(create_backup_job, respaldo.id)
        encolados.append(prog.id)

    return {"procesadas": len(encolados), "programacion_ids": encolados}


@router.get(
    "/{respaldo_id}/descargar",
    summary="Descargar respaldo",
    description="Verifica el hash SHA-256 antes de entregar el archivo de respaldo.",
)
async def download_backup(
    respaldo_id: str,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:descargar")),
    session: AsyncSession = Depends(get_session),
):
    respaldo = await _get_completed(session, respaldo_id)
    content = await asyncio.to_thread(storage().download, respaldo.ruta_storage)
    if hashlib.sha256(content).hexdigest() != respaldo.sha256:
        raise HTTPException(status_code=409, detail="El respaldo no superó la verificación SHA-256")
    await _audit(session, respaldo, user.id, "BACKUP_DOWNLOAD", "Respaldo descargado")
    filename = f"ssas-rrhh-{respaldo.fecha_creacion:%Y%m%d-%H%M%S}.tar.gz"
    return Response(
        content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/{respaldo_id}/verificar",
    response_model=VerificarIntegridadResponseSchema,
    summary="Verificar integridad de respaldo",
    description="Recalcula el hash SHA-256 leyendo el archivo desde almacenamiento y compara con el registrado.",
)
async def verify_backup_integrity(
    respaldo_id: str,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:ver")),
    session: AsyncSession = Depends(get_session),
):
    respaldo = await _get_completed(session, respaldo_id)
    content = await asyncio.to_thread(storage().download, respaldo.ruta_storage)
    calculado = hashlib.sha256(content).hexdigest()
    integro = bool(respaldo.sha256 and calculado.lower() == respaldo.sha256.lower())
    await _audit(
        session,
        respaldo,
        user.id,
        "BACKUP_VERIFY",
        f"Integridad verificada: {'VÁLIDA' if integro else 'CORRUPTA'}",
    )
    return VerificarIntegridadResponseSchema(
        id=respaldo.id,
        sha256_registrado=respaldo.sha256,
        sha256_calculado=calculado,
        integro=integro,
        tamano_bytes=len(content),
    )


@router.post(
    "/{respaldo_id}/restaurar",
    response_model=OperacionRespaldoSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Restaurar toda la base de datos",
    description="Programa una restauración destructiva tras validar su habilitación y confirmación.",
)
async def restore_backup(
    respaldo_id: str,
    request: RestaurarRespaldoSchema,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:restaurar")),
    session: AsyncSession = Depends(get_session),
):
    if not settings.backup_restore_enabled:
        raise HTTPException(status_code=403, detail="La restauración está deshabilitada en este entorno")
    if request.confirmacion != settings.backup_restore_confirmation:
        raise HTTPException(status_code=422, detail="La frase de confirmación no coincide")
    respaldo = await _get_completed(session, respaldo_id)
    respaldo.estado = "RESTAURACION_PENDIENTE"
    respaldo.restaurado_por_id = user.id
    await session.commit()
    background_tasks.add_task(restore_backup_job, respaldo.id, user.id)
    return OperacionRespaldoSchema(
        id=respaldo.id,
        estado=respaldo.estado,
        mensaje="La restauración fue programada; no operes el sistema hasta que finalice",
    )


@router.delete(
    "/{respaldo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar respaldo",
    description="Elimina el archivo privado y su registro, salvo que exista una operación en curso.",
)
async def delete_backup(
    respaldo_id: str,
    user: CurrentUser = Depends(require_platform_permission("platform:backup:eliminar")),
    session: AsyncSession = Depends(get_session),
):
    respaldo = await session.get(RespaldoModel, respaldo_id)
    if respaldo is None:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
    if respaldo.estado in {"PROCESANDO", "RESTAURANDO", "RESTAURACION_PENDIENTE"}:
        raise HTTPException(status_code=409, detail="No se puede eliminar una operación en curso")
    if respaldo.ruta_storage:
        await asyncio.to_thread(storage().delete, respaldo.ruta_storage)
    await _audit(session, respaldo, user.id, "BACKUP_DELETE", "Respaldo eliminado")
    await session.delete(respaldo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
