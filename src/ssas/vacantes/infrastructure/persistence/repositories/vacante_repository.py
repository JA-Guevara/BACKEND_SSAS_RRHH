from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
from ssas.vacantes.domain.entities.vacante import Vacante, VacanteHabilidadInfo
from ssas.vacantes.domain.entities.vacante_publica import VacantePublica
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import (
    VacanteHabilidadModel,
)
from ssas.vacantes.ports.outgoing.vacante_repository import VacanteRepository


def condiciones_vacante_vigente() -> list[Any]:
    """Condiciones que una vacante debe cumplir para operar de cara al público.

    Exige empresa viva (activa y sin borrado lógico) y vacante no vencida. Se comparte
    con el portal de postulaciones para que listar, consultar y postular apliquen
    exactamente el mismo criterio: la consulta debe hacerse con JOIN a ``empresa``.
    """
    return [
        EmpresaModel.activo.is_(True),
        EmpresaModel.eliminado_at.is_(None),
        (VacanteModel.fecha_cierre.is_(None) | (VacanteModel.fecha_cierre >= func.now())),
    ]


class SqlAlchemyVacanteRepository(VacanteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _query_options(self):
        return [
            selectinload(VacanteModel.cargo),
            selectinload(VacanteModel.departamento),
            selectinload(VacanteModel.habilidades_requeridas).selectinload(
                VacanteHabilidadModel.habilidad
            ),
        ]

    async def list_by_empresa(self, empresa_id: str, estado: str | None = None) -> list[Vacante]:
        conditions = [VacanteModel.empresa_id == empresa_id]
        if estado is not None:
            conditions.append(VacanteModel.estado == estado)
        result = await self.session.execute(
            select(VacanteModel)
            .options(*self._query_options())
            .where(*conditions)
            .order_by(VacanteModel.created_at.desc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, vacante_id: str, empresa_id: str) -> Vacante | None:
        result = await self.session.execute(
            select(VacanteModel)
            .options(*self._query_options())
            .where(
                VacanteModel.id == vacante_id,
                VacanteModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, empresa_id: str, responsable_id: str, values: dict[str, Any]) -> Vacante:
        values_copy = dict(values)
        habilidades_data = values_copy.pop("habilidades", None) or []
        model = VacanteModel(empresa_id=empresa_id, responsable_id=responsable_id, **values_copy)
        self.session.add(model)
        await self.session.flush()

        for h in habilidades_data:
            h_item = h if isinstance(h, dict) else h.model_dump()
            self.session.add(
                VacanteHabilidadModel(
                    vacante_id=model.id,
                    habilidad_id=h_item["habilidad_id"],
                    nivel_requerido=h_item["nivel_requerido"],
                    es_obligatorio=h_item.get("es_obligatorio", True),
                    peso=h_item.get("peso", 1.0),
                )
            )
        await self.session.flush()
        created = await self.get_by_id(model.id, empresa_id)
        if created is None:
            raise ValueError("No se pudo cargar la vacante creada")
        return created

    async def update(self, vacante_id: str, empresa_id: str, values: dict[str, Any]) -> Vacante:
        values_copy = dict(values)
        habilidades_data = values_copy.pop("habilidades", None)
        if values_copy:
            await self.session.execute(
                update(VacanteModel)
                .where(VacanteModel.id == vacante_id, VacanteModel.empresa_id == empresa_id)
                .values(**values_copy)
            )
        if habilidades_data is not None:
            await self.session.execute(
                delete(VacanteHabilidadModel).where(VacanteHabilidadModel.vacante_id == vacante_id)
            )
            for h in habilidades_data:
                h_item = h if isinstance(h, dict) else h.model_dump()
                self.session.add(
                    VacanteHabilidadModel(
                        vacante_id=vacante_id,
                        habilidad_id=h_item["habilidad_id"],
                        nivel_requerido=h_item["nivel_requerido"],
                        es_obligatorio=h_item.get("es_obligatorio", True),
                        peso=h_item.get("peso", 1.0),
                    )
                )
        await self.session.flush()
        model = await self.get_by_id(vacante_id, empresa_id)
        if model is None:
            raise ValueError("Vacante no encontrada")
        return model

    async def publish(self, vacante_id: str, empresa_id: str, fecha_publicacion: datetime) -> Vacante:
        await self.session.execute(
            update(VacanteModel)
            .where(VacanteModel.id == vacante_id, VacanteModel.empresa_id == empresa_id)
            .values(estado="PUBLICADA", fecha_publicacion=fecha_publicacion)
        )
        await self.session.flush()
        model = await self.get_by_id(vacante_id, empresa_id)
        if model is None:
            raise ValueError("Vacante no encontrada")
        return model

    async def cambiar_estado(self, vacante_id: str, empresa_id: str, estado: str) -> Vacante:
        await self.session.execute(
            update(VacanteModel)
            .where(VacanteModel.id == vacante_id, VacanteModel.empresa_id == empresa_id)
            .values(estado=estado)
        )
        await self.session.flush()
        model = await self.get_by_id(vacante_id, empresa_id)
        if model is None:
            raise ValueError("Vacante no encontrada")
        return model

    async def delete(self, vacante_id: str, empresa_id: str) -> None:
        await self.session.execute(
            delete(VacanteModel).where(
                VacanteModel.id == vacante_id,
                VacanteModel.empresa_id == empresa_id,
            )
        )
        await self.session.flush()

    async def references_belong_to_empresa(
        self, empresa_id: str, cargo_id: str, departamento_id: str, responsable_id: str
    ) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(CargoModel)
            .join(DepartamentoModel, DepartamentoModel.id == departamento_id)
            .join(UserModel, UserModel.id == responsable_id)
            .where(
                CargoModel.id == cargo_id,
                CargoModel.empresa_id == empresa_id,
                DepartamentoModel.empresa_id == empresa_id,
                UserModel.empresa_id == empresa_id,
            )
        )
        return result.scalar_one() == 1

    async def skills_belong_to_empresa(self, empresa_id: str, habilidad_ids: list[str]) -> bool:
        if not habilidad_ids:
            return True
        unique_ids = set(habilidad_ids)
        result = await self.session.execute(
            select(func.count(HabilidadModel.id)).where(
                HabilidadModel.empresa_id == empresa_id,
                HabilidadModel.id.in_(unique_ids),
                HabilidadModel.activo.is_(True),
            )
        )
        return result.scalar_one() == len(unique_ids)

    async def list_publicadas(
        self, empresa_slug: str, ubicacion: str | None, modalidad: str | None
    ) -> list[VacantePublica]:
        conditions = self._public_conditions(empresa_slug)
        if ubicacion:
            conditions.append(VacanteModel.ubicacion.ilike(f"%{ubicacion.strip()}%"))
        if modalidad:
            conditions.append(VacanteModel.modalidad == modalidad)
        result = await self.session.execute(
            select(VacanteModel, EmpresaModel.nombre_comercial)
            .options(*self._query_options())
            .join(EmpresaModel, EmpresaModel.id == VacanteModel.empresa_id)
            .where(*conditions)
            .order_by(VacanteModel.fecha_publicacion.desc())
        )
        return [self._to_public_entity(model, nombre) for model, nombre in result.all()]

    async def get_publicada(self, empresa_slug: str, vacante_id: str) -> VacantePublica | None:
        result = await self.session.execute(
            select(VacanteModel, EmpresaModel.nombre_comercial)
            .options(*self._query_options())
            .join(EmpresaModel, EmpresaModel.id == VacanteModel.empresa_id)
            .where(*self._public_conditions(empresa_slug), VacanteModel.id == vacante_id)
        )
        row = result.one_or_none()
        return self._to_public_entity(*row) if row else None

    @staticmethod
    def _public_conditions(empresa_slug: str) -> list[Any]:
        return [
            func.lower(EmpresaModel.slug) == empresa_slug.strip().lower(),
            VacanteModel.estado == "PUBLICADA",
            EmpresaModel.portal_publico_activo.is_(True),
            *condiciones_vacante_vigente(),
        ]

    @staticmethod
    def _to_public_entity(model: VacanteModel, empresa_nombre: str) -> VacantePublica:
        habilidades = [
            VacanteHabilidadInfo(
                habilidad_id=vh.habilidad_id,
                nombre=vh.habilidad.nombre if vh.habilidad else "",
                nivel_requerido=vh.nivel_requerido,
                es_obligatorio=vh.es_obligatorio,
                peso=vh.peso,
            )
            for vh in (model.habilidades_requeridas or [])
        ]
        return VacantePublica(
            id=model.id,
            empresa_nombre=empresa_nombre,
            titulo=model.titulo,
            descripcion=model.descripcion,
            requisitos=model.requisitos,
            beneficios=model.beneficios,
            cantidad_vacantes=model.cantidad_vacantes,
            salario_min=model.salario_min,
            salario_max=model.salario_max,
            mostrar_salario=model.mostrar_salario,
            modalidad=model.modalidad,
            ubicacion=model.ubicacion,
            experiencia_min=model.experiencia_min,
            fecha_publicacion=model.fecha_publicacion,
            fecha_cierre=model.fecha_cierre,
            cargo_nombre=model.cargo.nombre if model.cargo else None,
            departamento_nombre=model.departamento.nombre if model.departamento else None,
            habilidades=habilidades,
        )

    @staticmethod
    def _to_entity(model: VacanteModel) -> Vacante:
        habilidades = [
            VacanteHabilidadInfo(
                habilidad_id=vh.habilidad_id,
                nombre=vh.habilidad.nombre if vh.habilidad else "",
                nivel_requerido=vh.nivel_requerido,
                es_obligatorio=vh.es_obligatorio,
                peso=vh.peso,
            )
            for vh in (model.habilidades_requeridas or [])
        ]
        return Vacante(
            id=model.id,
            empresa_id=model.empresa_id,
            cargo_id=model.cargo_id,
            departamento_id=model.departamento_id,
            responsable_id=model.responsable_id,
            titulo=model.titulo,
            descripcion=model.descripcion,
            requisitos=model.requisitos,
            beneficios=model.beneficios,
            cantidad_vacantes=model.cantidad_vacantes,
            salario_min=model.salario_min,
            salario_max=model.salario_max,
            mostrar_salario=model.mostrar_salario,
            modalidad=model.modalidad,
            ubicacion=model.ubicacion,
            experiencia_min=model.experiencia_min,
            fecha_publicacion=model.fecha_publicacion,
            fecha_cierre=model.fecha_cierre,
            estado=model.estado,
            fecha_registro=model.fecha_registro,
            created_at=model.created_at,
            updated_at=model.updated_at,
            cargo_nombre=model.cargo.nombre if model.cargo else None,
            departamento_nombre=model.departamento.nombre if model.departamento else None,
            habilidades=habilidades,
        )

