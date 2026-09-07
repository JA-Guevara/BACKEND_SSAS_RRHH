from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.vacantes.domain.entities.vacante import Vacante
from ssas.vacantes.domain.entities.vacante_publica import VacantePublica
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.ports.outgoing.vacante_repository import VacanteRepository


class SqlAlchemyVacanteRepository(VacanteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_empresa(self, empresa_id: str, estado: str | None = None) -> list[Vacante]:
        conditions = [VacanteModel.empresa_id == empresa_id]
        if estado is not None:
            conditions.append(VacanteModel.estado == estado)
        result = await self.session.execute(
            select(VacanteModel).where(*conditions).order_by(VacanteModel.created_at.desc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, vacante_id: str, empresa_id: str) -> Vacante | None:
        result = await self.session.execute(
            select(VacanteModel).where(
                VacanteModel.id == vacante_id,
                VacanteModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, empresa_id: str, responsable_id: str, values: dict[str, Any]) -> Vacante:
        model = VacanteModel(empresa_id=empresa_id, responsable_id=responsable_id, **values)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, vacante_id: str, empresa_id: str, values: dict[str, Any]) -> Vacante:
        await self.session.execute(
            update(VacanteModel)
            .where(VacanteModel.id == vacante_id, VacanteModel.empresa_id == empresa_id)
            .values(**values)
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
            .join(EmpresaModel, EmpresaModel.id == VacanteModel.empresa_id)
            .where(*conditions)
            .order_by(VacanteModel.fecha_publicacion.desc())
        )
        return [self._to_public_entity(model, nombre) for model, nombre in result.all()]

    async def get_publicada(self, empresa_slug: str, vacante_id: str) -> VacantePublica | None:
        result = await self.session.execute(
            select(VacanteModel, EmpresaModel.nombre_comercial)
            .join(EmpresaModel, EmpresaModel.id == VacanteModel.empresa_id)
            .where(*self._public_conditions(empresa_slug), VacanteModel.id == vacante_id)
        )
        row = result.one_or_none()
        return self._to_public_entity(*row) if row else None

    @staticmethod
    def _public_conditions(empresa_slug: str) -> list[Any]:
        return [
            func.lower(EmpresaModel.slug) == empresa_slug.strip().lower(),
            EmpresaModel.activo.is_(True),
            VacanteModel.estado == "PUBLICADA",
            (VacanteModel.fecha_cierre.is_(None) | (VacanteModel.fecha_cierre >= func.now())),
        ]

    @staticmethod
    def _to_public_entity(model: VacanteModel, empresa_nombre: str) -> VacantePublica:
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
        )

    @staticmethod
    def _to_entity(model: VacanteModel) -> Vacante:
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
        )
