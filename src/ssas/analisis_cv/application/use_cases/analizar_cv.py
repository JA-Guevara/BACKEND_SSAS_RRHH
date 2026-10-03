from datetime import UTC, datetime
from decimal import Decimal
from time import monotonic
from uuid import UUID, uuid4

from sqlalchemy import or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ssas.analisis_cv.domain.analysis import (
    AnalisisCvError,
    calcular_afinidad,
    validar_evidencia,
)
from ssas.analisis_cv.infrastructure.extraction.cv_extractor import LocalCvExtractor
from ssas.analisis_cv.infrastructure.persistence.models.analisis_cv import AnalisisCvModel
from ssas.analisis_cv.infrastructure.providers.analysis_lock import analysis_lock, lock_persistence
from ssas.analisis_cv.infrastructure.providers.openai_provider import OpenAIAnalysisProvider
from ssas.analisis_cv.infrastructure.providers.privacy import redact_personal_data
from ssas.analisis_cv.ports.outgoing.analysis_provider import AnalysisProvider, CvExtractor
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulaciones.infrastructure.storage.local_cv_storage import LocalCvStorage
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.postulantes.infrastructure.persistence.models.postulante_habilidad import (
    PostulanteHabilidadModel,
)
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import VacanteHabilidadModel


async def _snapshot(session, postulacion_id, empresa_id, actor_id, *, lock=False):
    actor = await session.scalar(
        select(UserModel.id).where(
            UserModel.id == actor_id,
            UserModel.is_active.is_(True),
            UserModel.eliminado_at.is_(None),
            or_(UserModel.empresa_id == empresa_id, UserModel.empresa_id.is_(None)),
        )
    )
    if actor is None:
        raise AnalisisCvError("El actor no tiene acceso a esta empresa", 403)
    statement = (
        select(
            PostulacionModel.postulante_id,
            PostulacionModel.estado,
            PostulanteModel.cv_url,
            PostulanteModel.nombres,
            PostulanteModel.apellidos,
            PostulanteModel.ci,
            PostulanteModel.email,
            PostulanteModel.telefono,
            PostulanteModel.direccion,
            PostulanteModel.linkedin,
            VacanteModel.id.label("vacante_id"),
            VacanteModel.titulo,
            VacanteModel.descripcion,
            VacanteModel.requisitos,
            VacanteModel.experiencia_min,
        )
        .join(VacanteModel, PostulacionModel.vacante_id == VacanteModel.id)
        .join(
            PostulanteModel,
            PostulacionModel.postulante_id == PostulanteModel.id,
        )
        .where(
            PostulacionModel.id == postulacion_id,
            VacanteModel.empresa_id == empresa_id,
            PostulanteModel.empresa_id == empresa_id,
        )
    )
    row = (await session.execute(statement)).mappings().one_or_none()
    if row is None:
        raise AnalisisCvError("Postulacion no encontrada en la empresa", 404)
    if lock:
        # Match hiring's ordering; a joined FOR UPDATE gives no reliable lock order.
        await session.execute(
            select(VacanteModel.id)
            .where(
                VacanteModel.id == row["vacante_id"],
                VacanteModel.empresa_id == empresa_id,
            )
            .with_for_update()
        )
        await session.execute(
            select(PostulacionModel.id)
            .where(
                PostulacionModel.id == postulacion_id,
            )
            .with_for_update()
        )
        await session.execute(
            select(PostulanteModel.id)
            .where(
                PostulanteModel.id == row["postulante_id"],
                PostulanteModel.empresa_id == empresa_id,
            )
            .with_for_update()
        )
        row = (await session.execute(statement)).mappings().one_or_none()
        if row is None:
            raise AnalisisCvError("Postulacion no encontrada en la empresa", 404)
    if row["estado"] != "ACTIVA":
        raise AnalisisCvError("Solo se analizan postulaciones activas", 409)
    if not row["cv_url"]:
        raise AnalisisCvError("El postulante no tiene CV adjunto")
    codes = (
        (
            await session.execute(
                select(PostulacionModel.codigo_seguimiento)
                .join(
                    VacanteModel,
                    PostulacionModel.vacante_id == VacanteModel.id,
                )
                .where(
                    PostulacionModel.postulante_id == row["postulante_id"],
                    VacanteModel.empresa_id == empresa_id,
                )
            )
        )
        .scalars()
        .all()
    )
    if not LocalCvStorage.owns_cv(row["cv_url"], list(codes)):
        raise AnalisisCvError("El archivo CV no pertenece al postulante de esta empresa", 403)
    catalogo = (
        (
            await session.execute(
                select(
                    HabilidadModel.id.label("habilidad_id"),
                    HabilidadModel.nombre,
                )
                .where(HabilidadModel.empresa_id == empresa_id, HabilidadModel.activo.is_(True))
                .order_by(HabilidadModel.id)
            )
        )
        .mappings()
        .all()
    )
    requisitos = (
        (
            await session.execute(
                select(
                    VacanteHabilidadModel.habilidad_id,
                    VacanteHabilidadModel.peso,
                    VacanteHabilidadModel.nivel_requerido,
                    VacanteHabilidadModel.es_obligatorio,
                )
                .where(VacanteHabilidadModel.vacante_id == row["vacante_id"])
                .order_by(VacanteHabilidadModel.habilidad_id)
            )
        )
        .mappings()
        .all()
    )
    if not {r["habilidad_id"] for r in requisitos}.issubset({h["habilidad_id"] for h in catalogo}):
        raise AnalisisCvError("La vacante contiene habilidades inactivas o ajenas a la empresa")
    return dict(row), [dict(h) for h in catalogo], [dict(r) for r in requisitos]


async def _release_read_transaction(session: AsyncSession) -> None:
    if session.new or session.dirty or session.deleted:
        raise AnalisisCvError("El analisis requiere una sesion sin escrituras pendientes", 409)
    if session.in_transaction():
        # A flushed write is invisible in session.dirty; PostgreSQL's assigned XID detects it.
        with session.no_autoflush:
            xid = await session.scalar(text("SELECT txid_current_if_assigned()"))
        if xid is not None:
            raise AnalisisCvError(
                "El analisis no puede liberar una transaccion con escrituras", 409
            )
        await session.rollback()


async def analizar_cv(
    session: AsyncSession,
    postulacion_id: str,
    empresa_id: str,
    actor_id: str,
    *,
    source_ip: str | None = None,
    user_agent: str | None = None,
) -> AnalisisCvModel:
    """Caller enforces scoped permission/module policy and owns commit/rollback."""
    try:
        postulacion_id, empresa_id, actor_id = (
            str(UUID(str(value))) for value in (postulacion_id, empresa_id, actor_id)
        )
    except (ValueError, TypeError) as exc:
        raise AnalisisCvError("Los identificadores deben ser UUID validos") from exc
    if session.new or session.dirty or session.deleted:
        raise AnalisisCvError("El analisis requiere una sesion sin escrituras pendientes", 409)
    engine = session.bind
    if not isinstance(engine, AsyncEngine) or engine.dialect.name != "postgresql":
        raise AnalisisCvError("El analisis requiere una sesion ligada al engine PostgreSQL", 503)
    started = monotonic()
    await _release_read_transaction(session)
    async with AsyncSession(engine) as read_session:
        original = await _snapshot(read_session, postulacion_id, empresa_id, actor_id)
    max_slots = min(
        settings.ia_max_concurrent_analyses,
        max(1, settings.db_pool_size + settings.db_max_overflow - 2),
    )
    async with analysis_lock(engine, postulacion_id, max_slots=max_slots):
        row, catalogo, requisitos = original
        extractor: CvExtractor = LocalCvExtractor(settings)
        texto = await extractor.extract(row["cv_url"])
        texto = redact_personal_data(
            texto,
            [
                row[k]
                for k in (
                    "nombres",
                    "apellidos",
                    "ci",
                    "email",
                    "telefono",
                    "direccion",
                    "linkedin",
                )
            ],
        )
        vacante = {k: row[k] for k in ("titulo", "descripcion", "requisitos", "experiencia_min")}
        vacante["habilidades"] = [{**r, "peso": str(r["peso"])} for r in requisitos]
        provider: AnalysisProvider = OpenAIAnalysisProvider(settings)
        resultado = await provider.analyze(texto, vacante, catalogo)
        validar_evidencia(resultado, {h["habilidad_id"] for h in catalogo}, texto)
        score = calcular_afinidad(requisitos, resultado, row["experiencia_min"])
        names = {h["habilidad_id"]: h["nombre"] for h in catalogo}
        detected = [names[h.habilidad_id] for h in resultado.habilidades]
        ids = {h.habilidad_id for h in resultado.habilidades}
        missing = [names[r["habilidad_id"]] for r in requisitos if r["habilidad_id"] not in ids]
        # The persistence lock survives return until the caller commits or rolls back.
        async with session.begin_nested():
            await lock_persistence(session, postulacion_id)
            current = await _snapshot(session, postulacion_id, empresa_id, actor_id, lock=True)
            if current != original:
                raise AnalisisCvError(
                    "El CV o la vacante cambiaron durante el analisis; reintente", 409
                )
            model = AnalisisCvModel(
                id=str(uuid4()),
                postulacion_id=postulacion_id,
                puntaje_afinidad=score,
                habilidades_detectadas=detected,
                habilidades_faltantes=missing,
                anios_experiencia_detectados=Decimal(str(resultado.anios_experiencia)),
                resumen_ia=resultado.resumen,
                fortalezas=[h.evidencia for h in resultado.habilidades],
                observaciones=(
                    resultado.justificacion
                    + "\nEvidencia experiencia: "
                    + resultado.evidencia_experiencia
                ),
                modelo_usado=settings.ia_model,
                tiempo_proceso_ms=int((monotonic() - started) * 1000),
                fecha_analisis=datetime.now(UTC),
            )
            session.add(model)
            post = await session.get(PostulacionModel, postulacion_id, populate_existing=True)
            post.puntaje_ia = score
            for habilidad in resultado.habilidades:
                statement = insert(PostulanteHabilidadModel).values(
                    id=str(uuid4()),
                    postulante_id=row["postulante_id"],
                    habilidad_id=habilidad.habilidad_id,
                    nivel=habilidad.nivel,
                    anios_experiencia=0,
                    detectado_por_ia=True,
                )
                # Union of evidence across vacancies; manual entries are never overwritten.
                statement = statement.on_conflict_do_nothing(
                    index_elements=["postulante_id", "habilidad_id"],
                )
                await session.execute(statement)
            await RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)).execute(
                empresa_id=empresa_id,
                user_id=actor_id,
                module=AuditModule.SELECCION,
                action=AuditAction.CREATE,
                description="Analisis de CV completado",
                affected_table="analisis_cv",
                record_id=model.id,
                source_ip=source_ip,
                user_agent=user_agent,
                new_data={
                    "postulacion_id": postulacion_id,
                    "puntaje_afinidad": str(score),
                    "modelo_usado": settings.ia_model,
                },
            )
            await session.flush()
        return model
