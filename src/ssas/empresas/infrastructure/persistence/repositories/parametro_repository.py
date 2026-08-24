from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssas.empresas.domain.entities.parametro import ParametroEmpresa
from ssas.empresas.domain.exceptions import ParametroLegalNotFoundError
from ssas.empresas.infrastructure.persistence.models.parametro_legal import ParametroLegalModel
from ssas.empresas.infrastructure.persistence.models.parametro_valor import ParametroValorModel
from ssas.empresas.ports.outgoing.parametro_repository import ParametroRepository


class SqlAlchemyParametroRepository(ParametroRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_parametros_empresa(self, empresa_id: str) -> list[ParametroEmpresa]:
        result = await self.session.execute(
            select(ParametroLegalModel)
            .options(selectinload(ParametroLegalModel.valores))
            .where(ParametroLegalModel.activo.is_(True))
            .order_by(ParametroLegalModel.codigo)
        )
        parametros: list[ParametroEmpresa] = []
        for legal in result.scalars().all():
            valores_empresa = [valor for valor in legal.valores if valor.empresa_id == empresa_id]
            valores_empresa.sort(key=lambda valor: valor.vigente_desde, reverse=True)
            if valores_empresa:
                for valor in valores_empresa:
                    parametros.append(self._to_entity(legal, valor))
            else:
                parametros.append(self._to_entity(legal, None))
        return parametros

    async def get_parametro_legal_by_codigo(self, codigo: str) -> ParametroEmpresa | None:
        result = await self.session.execute(
            select(ParametroLegalModel).where(
                ParametroLegalModel.codigo == codigo.strip().upper(),
                ParametroLegalModel.activo.is_(True),
            )
        )
        legal = result.scalar_one_or_none()
        return self._to_entity(legal, None) if legal else None

    async def upsert_parametro_valor(
        self,
        empresa_id: str,
        codigo: str,
        valor: Decimal,
        vigente_desde: date,
        vigente_hasta: date | None,
        norma_legal: str | None,
    ) -> ParametroEmpresa:
        legal_result = await self.session.execute(
            select(ParametroLegalModel).where(
                ParametroLegalModel.codigo == codigo.strip().upper(),
                ParametroLegalModel.activo.is_(True),
            )
        )
        legal = legal_result.scalar_one_or_none()
        if legal is None:
            raise ParametroLegalNotFoundError("Parámetro legal no encontrado")

        same_start_result = await self.session.execute(
            select(ParametroValorModel).where(
                ParametroValorModel.empresa_id == empresa_id,
                ParametroValorModel.parametro_legal_id == legal.id,
                ParametroValorModel.vigente_desde == vigente_desde,
            )
        )
        model = same_start_result.scalar_one_or_none()
        if model is None:
            await self._close_previous_open_value(empresa_id, legal.id, vigente_desde)
            model = ParametroValorModel(
                empresa_id=empresa_id,
                parametro_legal_id=legal.id,
                valor=valor,
                vigente_desde=vigente_desde,
                vigente_hasta=vigente_hasta,
                norma_legal=norma_legal,
            )
            self.session.add(model)
        else:
            model.valor = valor
            model.vigente_hasta = vigente_hasta
            model.norma_legal = norma_legal

        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(legal, model)

    async def _close_previous_open_value(
        self,
        empresa_id: str,
        parametro_legal_id: str,
        vigente_desde: date,
    ) -> None:
        previous_end = vigente_desde - timedelta(days=1)
        await self.session.execute(
            update(ParametroValorModel)
            .where(
                ParametroValorModel.empresa_id == empresa_id,
                ParametroValorModel.parametro_legal_id == parametro_legal_id,
                ParametroValorModel.vigente_hasta.is_(None),
                ParametroValorModel.vigente_desde < vigente_desde,
            )
            .values(vigente_hasta=previous_end)
        )

    @staticmethod
    def _to_entity(
        legal: ParametroLegalModel,
        valor: ParametroValorModel | None,
    ) -> ParametroEmpresa:
        return ParametroEmpresa(
            codigo=legal.codigo,
            nombre=legal.nombre,
            tipo_valor=legal.tipo_valor,
            descripcion=legal.descripcion,
            valor_id=valor.id if valor else None,
            valor=valor.valor if valor else None,
            norma_legal=valor.norma_legal if valor else None,
            vigente_desde=valor.vigente_desde if valor else None,
            vigente_hasta=valor.vigente_hasta if valor else None,
            updated_at=valor.updated_at if valor else legal.updated_at,
        )