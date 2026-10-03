from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select

from ssas.empleados.infrastructure.persistence.models.empleado import EmpleadoModel
from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
from ssas.evaluaciones.infrastructure.persistence.models.evaluacion import EvaluacionModel
from ssas.postulaciones.domain.seleccion import (
    SeleccionError,
    transicion_entrevista,
    validar_agenda,
)
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel


class GestionarSeleccion:
    def __init__(self, repository):
        self.repository = repository
        self.session = repository.session

    async def guardar_entrevista(self, datos: dict, entrevista_id: str | None = None):
        datos = dict(datos)
        for key in ("postulacion_id", "entrevistador_id"):
            datos[key] = str(datos[key])
        validar_agenda(
            datos["fecha_hora"], datos["modalidad"], datos["enlace_reunion"], datos["lugar"]
        )
        if datos["fecha_hora"] <= datetime.now(UTC):
            raise SeleccionError("La entrevista debe programarse para una fecha futura", 422)
        post = await self.repository.postulacion(datos["postulacion_id"], lock=True)
        if post.estado != "ACTIVA":
            raise SeleccionError("La postulación no está activa")
        await self.repository.responsable(
            datos["entrevistador_id"], "entrevistas:registrar_resultado", lock=True
        )
        item = await self.repository.entrevista(entrevista_id, lock=True) if entrevista_id else None
        if item and (
            item.estado not in {"PROGRAMADA", "CONFIRMADA"} or item.postulacion_id != post.id
        ):
            raise SeleccionError("No se puede editar esta entrevista ni cambiar su postulación")
        await self.repository.sin_conflicto(
            datos["entrevistador_id"], datos["fecha_hora"], datos["duracion_min"], entrevista_id
        )
        if item is None:
            item = EntrevistaModel(id=str(uuid4()), estado="PROGRAMADA", **datos)
            self.session.add(item)
        else:
            for key, value in datos.items():
                setattr(item, key, value)
        await self.session.flush()
        return item

    async def estado_entrevista(self, id, estado):
        item = await self.repository.entrevista(id, lock=True)
        transicion_entrevista(item.estado, estado)
        if estado == "CONFIRMADA":
            post = await self.repository.postulacion(item.postulacion_id)
            if post.estado != "ACTIVA":
                raise SeleccionError("La postulación no está activa")
        item.estado = estado
        await self.session.flush()
        return item

    async def resultado_entrevista(self, id, datos):
        item = await self.repository.entrevista(id, lock=True)
        if item.fecha_hora > datetime.now(UTC):
            raise SeleccionError("La entrevista aún no comenzó")
        transicion_entrevista(item.estado, "REALIZADA")
        item.estado = "REALIZADA"
        for key, value in datos.items():
            setattr(item, key, value)
        await self.session.flush()
        return item

    async def guardar_evaluacion(self, post_id, datos, actor_id, evaluacion_id=None):
        post = await self.repository.postulacion(post_id, lock=True)
        if post.estado in {"RETIRADA", "DESCARTADA"}:
            raise SeleccionError("La postulación no permite registrar evaluaciones")
        item = await self.repository.evaluacion(evaluacion_id, lock=True) if evaluacion_id else None
        if item:
            for key, value in datos.items():
                setattr(item, key, value)
        else:
            # El evaluador es quien realiza la operación; no se acepta uno arbitrario del cliente.
            item = EvaluacionModel(
                id=str(uuid4()), postulacion_id=post.id, evaluador_id=actor_id, **datos
            )
            self.session.add(item)
        await self.session.flush()
        return item

    async def contratar(self, post_id, datos):
        post = await self.repository.postulacion(post_id)
        vacante = await self.repository.vacante(post.vacante_id, lock=True)
        post = await self.repository.postulacion(post_id, lock=True)
        if post.estado == "CONTRATADA" and post.empleado_id:
            empleado = await self.session.scalar(
                select(EmpleadoModel).where(
                    EmpleadoModel.id == post.empleado_id,
                    EmpleadoModel.empresa_id == self.repository.empresa_id,
                )
            )
            if empleado is None:
                raise SeleccionError("La contratación registrada no tiene un empleado válido")
            if empleado.codigo != datos["codigo"]:
                raise SeleccionError("Esta postulación ya fue contratada con otro código")
            return empleado
        if post.estado != "ACTIVA" or vacante.estado in {"CERRADA", "CANCELADA", "BORRADOR"}:
            raise SeleccionError("La vacante o postulación no permite contratar")
        count = await self.session.scalar(
            select(func.count())
            .select_from(PostulacionModel)
            .where(
                PostulacionModel.vacante_id == vacante.id, PostulacionModel.estado == "CONTRATADA"
            )
        )
        if count >= vacante.cantidad_vacantes:
            raise SeleccionError("La vacante ya tiene todos sus cupos cubiertos")
        candidato = await self.repository.postulante(post.postulante_id, lock=True)
        existente = await self.session.scalar(
            select(EmpleadoModel).where(
                EmpleadoModel.empresa_id == self.repository.empresa_id,
                func.lower(EmpleadoModel.ci) == candidato.ci.casefold(),
            )
        )
        if existente:
            raise SeleccionError("La persona ya está registrada como empleado de esta empresa")
        codigo = await self.session.scalar(
            select(EmpleadoModel.id).where(
                EmpleadoModel.empresa_id == self.repository.empresa_id,
                func.lower(EmpleadoModel.codigo) == datos["codigo"].casefold(),
            )
        )
        if codigo:
            raise SeleccionError("El código de empleado ya existe en la empresa")
        etapa = await self.session.scalar(
            select(EtapaReclutamientoModel)
            .where(
                EtapaReclutamientoModel.empresa_id == self.repository.empresa_id,
                EtapaReclutamientoModel.es_contratado.is_(True),
            )
            .order_by(EtapaReclutamientoModel.orden)
        )
        if etapa is None:
            raise SeleccionError("Configura una etapa de contratado para esta empresa")
        empleado = EmpleadoModel(
            id=str(uuid4()),
            empresa_id=self.repository.empresa_id,
            nombres=candidato.nombres,
            ci=candidato.ci,
            telefono=candidato.telefono,
            direccion=candidato.direccion,
            email_personal=candidato.email,
            fecha_nacimiento=candidato.fecha_nacimiento,
            estado="ACTIVO",
            **datos,
        )
        self.session.add(empleado)
        await self.session.flush()
        post.empleado_id, post.estado, post.etapa_id = empleado.id, "CONTRATADA", etapa.id
        post.motivo_rechazo_id = None
        post.fecha_ultimo_cambio = datetime.now(UTC)
        if count + 1 == vacante.cantidad_vacantes:
            vacante.estado = "CERRADA"
            vacante.fecha_cierre = datetime.now(UTC)
        await self.session.flush()
        return empleado

    async def banco(self, id, incluir):
        candidate = await self.repository.postulante(id)
        candidate.en_banco_talento = incluir
        await self.session.flush()
        return candidate

    async def asociar(self, id, vacante_id):
        candidate = await self.repository.postulante(id)
        vacante = await self.repository.vacante(vacante_id, lock=True)
        if not candidate.en_banco_talento:
            raise SeleccionError("El postulante no pertenece al banco de talentos")
        if vacante.estado != "PUBLICADA":
            raise SeleccionError("Selecciona una vacante publicada")
        existing = await self.session.scalar(
            select(PostulacionModel).where(
                PostulacionModel.vacante_id == vacante.id,
                PostulacionModel.postulante_id == candidate.id,
            )
        )
        if existing:
            return existing
        etapa = await self.session.scalar(
            select(EtapaReclutamientoModel)
            .where(
                EtapaReclutamientoModel.empresa_id == self.repository.empresa_id,
                EtapaReclutamientoModel.es_inicial.is_(True),
            )
            .order_by(EtapaReclutamientoModel.orden)
        )
        if etapa is None:
            raise SeleccionError("La empresa no tiene una etapa inicial")
        post = PostulacionModel(
            id=str(uuid4()),
            vacante_id=vacante.id,
            postulante_id=candidate.id,
            etapa_id=etapa.id,
            estado="ACTIVA",
            codigo_seguimiento=f"SSAS-{uuid4().hex[:20].upper()}",
        )
        self.session.add(post)
        await self.session.flush()
        return post
