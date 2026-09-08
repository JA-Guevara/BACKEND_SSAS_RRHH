from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.departamentos.domain.entities.departamento import Departamento
from ssas.departamentos.domain.exceptions import DepartamentoNotFoundError
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
from ssas.departamentos.ports.outgoing.departamento_repository import DepartamentoRepository


class SqlAlchemyDepartamentoRepository(DepartamentoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_departamentos(
        self, empresa_id: str, activo: bool | None = None
    ) -> list[Departamento]:
        conditions = [DepartamentoModel.empresa_id == empresa_id]
        if activo is not None:
            conditions.append(DepartamentoModel.activo.is_(activo))
        result = await self.session.execute(
            select(DepartamentoModel).where(*conditions).order_by(DepartamentoModel.nombre)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, departamento_id: str, empresa_id: str) -> Departamento | None:
        result = await self.session.execute(
            select(DepartamentoModel).where(
                DepartamentoModel.id == departamento_id,
                DepartamentoModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_nombre(self, nombre: str, empresa_id: str) -> Departamento | None:
        result = await self.session.execute(
            select(DepartamentoModel).where(
                DepartamentoModel.empresa_id == empresa_id,
                func.lower(DepartamentoModel.nombre) == nombre.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists(self, departamento_id: str, empresa_id: str) -> bool:
        result = await self.session.execute(
            select(func.count(DepartamentoModel.id)).where(
                DepartamentoModel.id == departamento_id,
                DepartamentoModel.empresa_id == empresa_id,
            )
        )
        return result.scalar_one() > 0

    async def has_dependencies(self, departamento_id: str, empresa_id: str) -> bool:
        result = await self.session.execute(
            select(func.count(CargoModel.id)).where(
                CargoModel.departamento_id == departamento_id,
                CargoModel.empresa_id == empresa_id,
            )
        )
        return result.scalar_one() > 0

    async def create_departamento(
        self,
        empresa_id: str,
        nombre: str,
        descripcion: str | None,
        activo: bool,
        codigo: str | None = None,
        departamento_padre_id: str | None = None,
        responsable_id: str | None = None,
    ) -> Departamento:
        model = DepartamentoModel(
            empresa_id=empresa_id,
            nombre=nombre,
            codigo=codigo.strip().upper() if codigo else None,
            descripcion=descripcion,
            departamento_padre_id=departamento_padre_id,
            responsable_id=responsable_id,
            activo=activo,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update_departamento(
        self, departamento_id: str, empresa_id: str, values: dict
    ) -> Departamento:
        clean_values = dict(values)
        if "codigo" in clean_values and clean_values["codigo"]:
            clean_values["codigo"] = clean_values["codigo"].strip().upper()
        await self.session.execute(
            update(DepartamentoModel)
            .where(
                DepartamentoModel.id == departamento_id,
                DepartamentoModel.empresa_id == empresa_id,
            )
            .values(**clean_values)
        )
        await self.session.flush()
        departamento = await self.get_by_id(departamento_id, empresa_id)
        if departamento is None:
            raise DepartamentoNotFoundError("Departamento no encontrado")
        return departamento

    async def delete_departamento(self, departamento_id: str, empresa_id: str) -> None:
        await self.session.execute(
            delete(DepartamentoModel).where(
                DepartamentoModel.id == departamento_id,
                DepartamentoModel.empresa_id == empresa_id,
            )
        )
        await self.session.flush()

    @staticmethod
    def _to_entity(model: DepartamentoModel) -> Departamento:
        return Departamento(
            id=model.id,
            empresa_id=model.empresa_id,
            nombre=model.nombre,
            codigo=model.codigo,
            descripcion=model.descripcion,
            departamento_padre_id=model.departamento_padre_id,
            responsable_id=model.responsable_id,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

