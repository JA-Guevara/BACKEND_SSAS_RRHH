from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.analisis_cv.infrastructure.persistence.models.analisis_cv import AnalisisCvModel
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
from ssas.evaluaciones.infrastructure.persistence.models.evaluacion import EvaluacionModel
from ssas.postulaciones.domain.seleccion import SeleccionError
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion_nota import (
    PostulacionNotaModel,
)
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.roles.infrastructure.persistence.repositories.authorization_repository import (
    SqlAlchemyAuthorizationRepository,
)
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel


class SeleccionRepository:
    def __init__(self, session: AsyncSession, empresa_id: str):
        self.session = session
        self.empresa_id = empresa_id

    async def postulacion(self, id: str, lock: bool = False):
        query = (
            select(PostulacionModel)
            .join(VacanteModel)
            .join(PostulanteModel)
            .where(
                PostulacionModel.id == id,
                VacanteModel.empresa_id == self.empresa_id,
                PostulanteModel.empresa_id == self.empresa_id,
            )
        )
        if lock:
            query = query.with_for_update(of=PostulacionModel).execution_options(
                populate_existing=True
            )
        item = await self.session.scalar(query)
        if item is None:
            raise SeleccionError("Postulación no encontrada", 404)
        return item

    async def vacante(self, id: str, lock: bool = False):
        query = select(VacanteModel).where(
            VacanteModel.id == id, VacanteModel.empresa_id == self.empresa_id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        item = await self.session.scalar(query)
        if item is None:
            raise SeleccionError("Vacante no encontrada", 404)
        return item

    async def postulante(self, id: str, lock: bool = False):
        query = select(PostulanteModel).where(
            PostulanteModel.id == id, PostulanteModel.empresa_id == self.empresa_id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        item = await self.session.scalar(query)
        if item is None:
            raise SeleccionError("Postulante no encontrado", 404)
        return item

    async def responsable(self, id: str, capacidad: str, lock: bool = False):
        query = select(UserModel).where(
            UserModel.id == id,
            UserModel.empresa_id == self.empresa_id,
            UserModel.is_active.is_(True),
            UserModel.eliminado_at.is_(None),
        )
        if lock:
            query = query.with_for_update()
        user = await self.session.scalar(query)
        if user is None:
            raise SeleccionError("El responsable no pertenece a la empresa o está inactivo", 422)
        codes = await SqlAlchemyAuthorizationRepository(self.session).get_user_permission_codes(
            id, self.empresa_id
        )
        if capacidad not in codes:
            raise SeleccionError("El responsable no tiene capacidad para realizar esa tarea", 422)
        return user

    async def entrevista(self, id: str, lock: bool = False):
        query = (
            select(EntrevistaModel)
            .join(PostulacionModel)
            .join(VacanteModel)
            .where(EntrevistaModel.id == id, VacanteModel.empresa_id == self.empresa_id)
        )
        if lock:
            query = query.with_for_update(of=EntrevistaModel).execution_options(
                populate_existing=True
            )
        item = await self.session.scalar(query)
        if item is None:
            raise SeleccionError("Entrevista no encontrada", 404)
        return item

    async def evaluacion(self, id: str, lock: bool = False):
        query = (
            select(EvaluacionModel)
            .join(PostulacionModel)
            .join(VacanteModel)
            .where(EvaluacionModel.id == id, VacanteModel.empresa_id == self.empresa_id)
        )
        if lock:
            query = query.with_for_update(of=EvaluacionModel).execution_options(
                populate_existing=True
            )
        item = await self.session.scalar(query)
        if item is None:
            raise SeleccionError("Evaluación no encontrada", 404)
        return item

    async def sin_conflicto(self, responsable_id, fecha, duracion, excluir=None):
        # La fila del responsable permanece bloqueada hasta el commit de la petición.
        query = select(EntrevistaModel).where(
            EntrevistaModel.entrevistador_id == responsable_id,
            EntrevistaModel.estado.in_(["PROGRAMADA", "CONFIRMADA"]),
            EntrevistaModel.fecha_hora < fecha + timedelta(minutes=duracion),
        )
        if excluir:
            query = query.where(EntrevistaModel.id != excluir)
        for item in (await self.session.scalars(query)).all():
            if item.fecha_hora + timedelta(minutes=item.duracion_min or 45) > fecha:
                raise SeleccionError("El entrevistador ya tiene una entrevista en ese horario")

    async def agenda(self, estado, desde, hasta, postulacion_id, offset, limit):
        conditions = [VacanteModel.empresa_id == self.empresa_id]
        for column, value in [
            (EntrevistaModel.estado, estado),
            (EntrevistaModel.postulacion_id, postulacion_id),
        ]:
            if value:
                conditions.append(column == value)
        if desde:
            conditions.append(EntrevistaModel.fecha_hora >= desde)
        if hasta:
            conditions.append(EntrevistaModel.fecha_hora <= hasta)
        query = select(
            EntrevistaModel,
            PostulanteModel.nombres,
            PostulanteModel.apellidos,
            UserModel.name,
            UserModel.apellido,
        ).select_from(EntrevistaModel)
        query = (
            query.join(PostulacionModel)
            .join(VacanteModel)
            .join(PostulanteModel, PostulanteModel.id == PostulacionModel.postulante_id)
            .join(UserModel, UserModel.id == EntrevistaModel.entrevistador_id)
            .where(*conditions)
        )
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.session.execute(
            query.order_by(EntrevistaModel.fecha_hora, EntrevistaModel.id)
            .offset(offset)
            .limit(limit)
        )
        items = []
        for item, nombres, apellidos, nombre, apellido in result.all():
            item.nombre_postulante = f"{nombres} {apellidos}"
            item.entrevistador_nombre = f"{nombre} {apellido}"
            items.append(item)
        return {"items": items, "total": total}

    async def responsables(self, capacidad):
        users = (
            await self.session.scalars(
                select(UserModel)
                .where(
                    UserModel.empresa_id == self.empresa_id,
                    UserModel.is_active.is_(True),
                    UserModel.eliminado_at.is_(None),
                )
                .order_by(UserModel.name)
            )
        ).all()
        entrevistadores = []
        for user in users:
            codes = await SqlAlchemyAuthorizationRepository(self.session).get_user_permission_codes(
                user.id, self.empresa_id
            )
            if capacidad in codes:
                entrevistadores.append(
                    {
                        "id": user.id,
                        "nombre": f"{user.name} {user.apellido}",
                        "rol": "Responsable",
                    }
                )
        return entrevistadores

    async def opciones(self):
        entrevistadores = await self.responsables("entrevistas:registrar_resultado")
        posts = (
            await self.session.execute(
                select(PostulacionModel, PostulanteModel, VacanteModel)
                .select_from(PostulacionModel)
                .join(PostulanteModel)
                .join(VacanteModel)
                .where(
                    VacanteModel.empresa_id == self.empresa_id,
                    PostulanteModel.empresa_id == self.empresa_id,
                    PostulacionModel.estado == "ACTIVA",
                )
                .order_by(PostulanteModel.nombres)
            )
        ).all()
        return {
            "entrevistadores": entrevistadores,
            "postulaciones": [
                {"id": p.id, "nombre_postulante": f"{c.nombres} {c.apellidos}", "vacante": v.titulo}
                for p, c, v in posts
            ],
        }

    async def evaluaciones(self, keys):
        rows = (
            await self.session.execute(
                select(EvaluacionModel, UserModel.name, UserModel.apellido)
                .join(UserModel, UserModel.id == EvaluacionModel.evaluador_id)
                .where(EvaluacionModel.postulacion_id.in_(keys))
                .order_by(EvaluacionModel.fecha.desc(), EvaluacionModel.id)
            )
        ).all()
        output = []
        for item, name, apellido in rows:
            item.evaluador_nombre = f"{name} {apellido}"
            output.append(item)
        return output

    async def candidatos(self, vacante_id: str, ids: list[str] | None = None):
        await self.vacante(vacante_id)
        query = (
            select(PostulacionModel, PostulanteModel)
            .join(PostulanteModel)
            .where(
                PostulacionModel.vacante_id == vacante_id,
                PostulanteModel.empresa_id == self.empresa_id,
            )
        )
        if ids is not None:
            query = query.where(PostulacionModel.id.in_(ids))
        rows = (await self.session.execute(query)).all()
        if ids is not None and len(rows) != len(ids):
            raise SeleccionError("Los finalistas deben pertenecer a la misma vacante", 422)
        keys = [p.id for p, _ in rows]
        analyses = (
            await self.session.scalars(
                select(AnalisisCvModel)
                .where(AnalisisCvModel.postulacion_id.in_(keys))
                .order_by(AnalisisCvModel.fecha_analisis.desc(), AnalisisCvModel.id.desc())
            )
        ).all()
        interviews = (
            await self.session.scalars(
                select(EntrevistaModel)
                .where(EntrevistaModel.postulacion_id.in_(keys))
                .order_by(EntrevistaModel.fecha_hora.desc())
            )
        ).all()
        evaluations = await self.evaluaciones(keys)
        latest, inter, evals = {}, {}, {}
        for item in analyses:
            latest.setdefault(item.postulacion_id, item)
        for item in interviews:
            inter.setdefault(item.postulacion_id, []).append(item)
        for item in evaluations:
            evals.setdefault(item.postulacion_id, []).append(item)
        output = []
        for post, candidate in rows:
            analysis = latest.get(post.id)
            ints, evs = inter.get(post.id, []), evals.get(post.id, [])
            normalized = [float(e.puntaje / e.puntaje_maximo * 100) for e in evs]
            scores = [float(e.puntaje) for e in ints if e.puntaje is not None]
            output.append(
                {
                    "id": post.id,
                    "postulante_id": candidate.id,
                    "nombre_postulante": f"{candidate.nombres} {candidate.apellidos}",
                    "estado": post.estado,
                    "experiencia_anios": candidate.anios_experiencia,
                    "educacion": candidate.nivel_educativo,
                    "puntaje_ia": float(post.puntaje_ia) if post.puntaje_ia is not None else None,
                    "puntaje_manual": float(post.puntaje_manual)
                    if post.puntaje_manual is not None
                    else None,
                    "puntaje_evaluaciones": sum(normalized) / len(normalized)
                    if normalized
                    else None,
                    "puntaje_entrevistas": sum(scores) / len(scores) if scores else None,
                    "habilidades_detectadas": analysis.habilidades_detectadas if analysis else [],
                    "habilidades_faltantes": analysis.habilidades_faltantes if analysis else [],
                    "entrevistas": ints,
                    "evaluaciones": evs,
                    "_fecha": post.fecha_postulacion,
                }
            )
        return output

    async def historial(self, postulacion_id):
        post = await self.postulacion(postulacion_id)
        items = []
        for model, fecha, tipo, responsable in [
            (EntrevistaModel, "fecha_hora", "ENTREVISTA", "entrevistador_id"),
            (EvaluacionModel, "fecha", "EVALUACION", "evaluador_id"),
            (AnalisisCvModel, "fecha_analisis", "ANALISIS_CV", None),
            (PostulacionNotaModel, "created_at", "NOTA", "usuario_id"),
        ]:
            records = (
                await self.session.scalars(
                    select(model).where(model.postulacion_id == postulacion_id)
                )
            ).all()
            for item in records:
                items.append(
                    {
                        "id": item.id,
                        "tipo": tipo,
                        "fecha": getattr(item, fecha),
                        "responsable": getattr(item, responsable) if responsable else "IA",
                        "puntaje": getattr(
                            item, "puntaje", getattr(item, "puntaje_afinidad", None)
                        ),
                        "recomendacion": getattr(item, "recomendacion", "") or "",
                        "observaciones": getattr(
                            item, "observaciones", getattr(item, "contenido", "")
                        )
                        or "",
                    }
                )
        audits = (
            await self.session.scalars(
                select(AuditLogModel).where(
                    AuditLogModel.empresa_id == self.empresa_id,
                    AuditLogModel.tabla_afectada == "postulacion",
                    AuditLogModel.registro_id == post.id,
                )
            )
        ).all()
        for event in audits:
            items.append(
                {
                    "id": event.id,
                    "tipo": event.action,
                    "fecha": event.fecha,
                    "responsable": event.user_id or event.actor_label or "Sistema",
                    "observaciones": event.description,
                }
            )
        user_ids = {item["responsable"] for item in items if len(item["responsable"]) == 36}
        names = {
            u.id: f"{u.name} {u.apellido}"
            for u in (
                await self.session.scalars(select(UserModel).where(UserModel.id.in_(user_ids)))
            ).all()
        }
        for item in items:
            item["responsable"] = names.get(item["responsable"], item["responsable"])
        return sorted(items, key=lambda item: (item["fecha"], item["id"]), reverse=True)
