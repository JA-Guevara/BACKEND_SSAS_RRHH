from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.cargos.domain.entities.cargo import Cargo
from ssas.cargos.domain.exceptions import CargoNotFoundError
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.cargos.ports.outgoing.cargo_repository import CargoRepository
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel


class SqlAlchemyCargoRepository(CargoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_cargos(
        self,
        empresa_id: str,
        activo: bool | None = None,
        departamento_id: str | None = None,
    ) -> list[Cargo]:
        conditions = [CargoModel.empresa_id == empresa_id]
        if activo is not None:
            conditions.append(CargoModel.activo.is_(activo))
        if departamento_id is not None:
            conditions.append(CargoModel.departamento_id == departamento_id)
        result = await self.session.execute(
            select(CargoModel).where(*conditions).order_by(CargoModel.nombre)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, cargo_id: str, empresa_id: str) -> Cargo | None:
        result = await self.session.execute(
            select(CargoModel).where(
                CargoModel.id == cargo_id,
                CargoModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_nombre(self, nombre: str, empresa_id: str) -> Cargo | None:
        result = await self.session.execute(
            select(CargoModel).where(
                CargoModel.empresa_id == empresa_id,
                func.lower(CargoModel.nombre) == nombre.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists(self, cargo_id: str, empresa_id: str) -> bool:
        result = await self.session.execute(
            select(func.count(CargoModel.id)).where(
                CargoModel.id == cargo_id,
                CargoModel.empresa_id == empresa_id,
            )
        )
        return result.scalar_one() > 0

    async def departamento_exists(self, departamento_id: str, empresa_id: str) -> bool:
        result = await self.session.execute(
            select(func.count(DepartamentoModel.id)).where(
                DepartamentoModel.id == departamento_id,
                DepartamentoModel.empresa_id == empresa_id,
            )
        )
        return result.scalar_one() > 0

    async def has_dependencies(self, cargo_id: str, empresa_id: str) -> bool:
        # T1-04/T1-06 conectarán vacantes/postulaciones. Por ahora cargo no tiene hijos.
        return False

    async def create_cargo(
        self,
        empresa_id: str,
        nombre: str,
        departamento_id: str | None,
        descripcion: str | None,
        activo: bool,
    ) -> Cargo:
        model = CargoModel(
            empresa_id=empresa_id,
            departamento_id=departamento_id,
            nombre=nombre,
            descripcion=descripcion,
            activo=activo,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update_cargo(self, cargo_id: str, empresa_id: str, values: dict) -> Cargo:
        await self.session.execute(
            update(CargoModel)
            .where(
                CargoModel.id == cargo_id,
                CargoModel.empresa_id == empresa_id,
            )
            .values(**values)
        )
        await self.session.flush()
        cargo = await self.get_by_id(cargo_id, empresa_id)
        if cargo is None:
            raise CargoNotFoundError("Cargo no encontrado")
        return cargo

    async def delete_cargo(self, cargo_id: str, empresa_id: str) -> None:
        await self.session.execute(
            delete(CargoModel).where(
                CargoModel.id == cargo_id,
                CargoModel.empresa_id == empresa_id,
            )
        )
        await self.session.flush()

    @staticmethod
    def _to_entity(model: CargoModel) -> Cargo:
        return Cargo(
            id=model.id,
            empresa_id=model.empresa_id,
            departamento_id=model.departamento_id,
            nombre=model.nombre,
            descripcion=model.descripcion,
            nivel=model.nivel,
            salario_min=model.salario_min,
            salario_max=model.salario_max,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
