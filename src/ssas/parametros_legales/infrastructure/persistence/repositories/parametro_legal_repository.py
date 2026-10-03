from datetime import date
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.parametros_legales.domain.entities.parametro_legal import ParametroLegal
from ssas.parametros_legales.domain.exceptions import ParametroLegalNotFoundError
from ssas.parametros_legales.infrastructure.persistence.models.parametro_legal import (
    ParametroLegalModel,
)
from ssas.parametros_legales.ports.outgoing.parametro_legal_repository import (
    ParametroLegalRepository,
)


class SqlAlchemyParametroLegalRepository(ParametroLegalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_empresa(self, empresa_id: str) -> list[ParametroLegal]:
        result = await self.session.execute(
            select(ParametroLegalModel)
            .where(ParametroLegalModel.empresa_id == empresa_id)
            .order_by(ParametroLegalModel.vigencia_desde.desc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, periodo_id: str, empresa_id: str) -> ParametroLegal | None:
        result = await self.session.execute(
            select(ParametroLegalModel).where(
                ParametroLegalModel.id == periodo_id,
                ParametroLegalModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_overlap(
        self,
        empresa_id: str,
        vigencia_desde: date,
        vigencia_hasta: date,
        exclude_id: str | None = None,
    ) -> ParametroLegal | None:
        conditions = [
            ParametroLegalModel.empresa_id == empresa_id,
            ParametroLegalModel.vigencia_desde <= vigencia_hasta,
            ParametroLegalModel.vigencia_hasta >= vigencia_desde,
        ]
        if exclude_id is not None:
            conditions.append(ParametroLegalModel.id != exclude_id)
        result = await self.session.execute(
            select(ParametroLegalModel)
            .where(and_(*conditions))
            .order_by(ParametroLegalModel.vigencia_desde.asc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, empresa_id: str, values: dict[str, Any]) -> ParametroLegal:
        model = ParametroLegalModel(empresa_id=empresa_id, **values)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(
        self, periodo_id: str, empresa_id: str, values: dict[str, Any]
    ) -> ParametroLegal:
        await self.session.execute(
            update(ParametroLegalModel)
            .where(
                ParametroLegalModel.id == periodo_id,
                ParametroLegalModel.empresa_id == empresa_id,
            )
            .values(**values),
        )
        await self.session.flush()
        result = await self.session.execute(
            select(ParametroLegalModel).where(
                ParametroLegalModel.id == periodo_id,
                ParametroLegalModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ParametroLegalNotFoundError("Periodo de parámetros no encontrado")
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: ParametroLegalModel) -> ParametroLegal:
        return ParametroLegal(
            id=model.id,
            empresa_id=model.empresa_id,
            vigencia_desde=model.vigencia_desde,
            vigencia_hasta=model.vigencia_hasta,
            afp=model.afp,
            aporte_solidario=model.aporte_solidario,
            rc_iva=model.rc_iva,
            aguinaldo=model.aguinaldo,
            prima=model.prima,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )