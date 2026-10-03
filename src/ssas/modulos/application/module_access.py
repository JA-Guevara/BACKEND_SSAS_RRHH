"""Reglas de acceso a módulos por empresa.

Un módulo está disponible para una empresa cuando es ``es_core`` (administración
básica, no se puede desactivar) o cuando existe una habilitación explícita en
``empresa_modulo``. Los administradores de plataforma no tienen empresa y por eso
nunca se les filtra.
"""

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.modulos.infrastructure.persistence.models.empresa_modulo import EmpresaModuloModel
from ssas.modulos.infrastructure.persistence.models.modulo import ModuloModel


async def get_modulos_habilitados(session: AsyncSession, empresa_id: str) -> list[str]:
    """Códigos de módulo disponibles para la empresa, ordenados por ``orden``."""
    statement = (
        select(ModuloModel.codigo)
        .outerjoin(
            EmpresaModuloModel,
            and_(
                EmpresaModuloModel.modulo_id == ModuloModel.id,
                EmpresaModuloModel.empresa_id == empresa_id,
            ),
        )
        .where(
            ModuloModel.activo.is_(True),
            or_(ModuloModel.es_core.is_(True), EmpresaModuloModel.habilitado.is_(True)),
        )
        .order_by(ModuloModel.orden, ModuloModel.codigo)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())
