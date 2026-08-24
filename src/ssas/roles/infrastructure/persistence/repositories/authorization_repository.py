from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.roles.infrastructure.persistence.models.permission import PermissionModel
from ssas.roles.infrastructure.persistence.models.role import RoleModel
from ssas.roles.infrastructure.persistence.models.role_permission import rol_permiso_table
from ssas.roles.infrastructure.persistence.models.user_role import usuario_rol_table
from ssas.roles.ports.outgoing.authorization_repository import AuthorizationRepository


class SqlAlchemyAuthorizationRepository(AuthorizationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_permission_codes(self, user_id: str, empresa_id: str) -> set[str]:
        statement = (
            select(PermissionModel.name)
            .select_from(UserModel)
            .join(EmpresaModel, EmpresaModel.id == UserModel.empresa_id)
            .join(usuario_rol_table, usuario_rol_table.c.usuario_id == UserModel.id)
            .join(RoleModel, RoleModel.id == usuario_rol_table.c.rol_id)
            .join(rol_permiso_table, rol_permiso_table.c.rol_id == RoleModel.id)
            .join(PermissionModel, PermissionModel.id == rol_permiso_table.c.permiso_id)
            .where(
                UserModel.id == user_id,
                UserModel.empresa_id == empresa_id,
                EmpresaModel.id == empresa_id,
                EmpresaModel.activo.is_(True),
                UserModel.is_active.is_(True),
                RoleModel.is_active.is_(True),
                RoleModel.empresa_id == empresa_id,
            )
        )
        result = await self.session.execute(statement)
        return set(result.scalars().all())