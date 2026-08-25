import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.domain.password_policy import validate_password
from ssas.auth.infrastructure.persistence.models.email_verification_token import (
    EmailVerificationTokenModel,
)
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.config.settings import settings
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.platform.domain.exceptions import PlatformConflictError
from ssas.platform.infrastructure.persistence.repositories.platform_repository import (
    PlatformRepository,
)
from ssas.roles.infrastructure.persistence.models.permission import PermissionModel
from ssas.roles.infrastructure.persistence.models.role import RoleModel
from ssas.roles.infrastructure.persistence.models.role_permission import rol_permiso_table
from ssas.roles.infrastructure.persistence.models.user_role import usuario_rol_table

ROLE_DEFINITIONS: tuple[tuple[str, str, tuple[str, ...] | None], ...] = (
    ("ADMIN_EMPRESA", "Administrador de Empresa", None),
    (
        "RRHH",
        "Recursos Humanos",
        ("usuarios:ver", "usuarios:crear", "usuarios:editar", "bitacora:ver"),
    ),
    ("RECLUTADOR", "Reclutador", ("vacantes:gestionar", "candidatos:gestionar")),
    ("EMPLEADO", "Empleado", ()),
)


PREFIJO_PLATAFORMA = "platform:"


class ProvisionEmpresa:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PlatformRepository(session)
        self.password_hasher = Argon2PasswordHasher()

    async def execute(self, request) -> tuple[EmpresaModel, UserModel, str]:
        empresa_data = request.empresa.model_dump()
        empresa_data["slug"] = empresa_data["slug"].strip().lower()
        if empresa_data.get("nit"):
            empresa_data["nit"] = empresa_data["nit"].strip()
        if await self.repository.get_empresa_by_unique(
            empresa_data.get("nit"), empresa_data["slug"]
        ):
            raise PlatformConflictError("Ya existe una empresa con ese NIT o slug")
        admin_data = request.administrador.model_dump()
        email = str(admin_data["email"]).strip().lower()
        username = admin_data["username"].strip().lower()
        validate_password(admin_data["password"], username, email)

        empresa = EmpresaModel(**empresa_data, activo=True)
        self.session.add(empresa)
        await self.session.flush()
        # Un rol de empresa NUNCA puede recibir permisos de plataforma: son operaciones
        # del proveedor SaaS (crear empresas y gestionar administradores globales).
        # Sin este filtro, ADMIN_EMPRESA —que se define con "todos los permisos"— se
        # llevaría también los platform:*.
        permissions = [
            permiso
            for permiso in (await self.session.execute(select(PermissionModel))).scalars().all()
            if not permiso.name.startswith(PREFIJO_PLATAFORMA)
        ]
        permission_by_code = {permission.name: permission for permission in permissions}
        roles: dict[str, RoleModel] = {}
        for code, name, permission_codes in ROLE_DEFINITIONS:
            role = RoleModel(
                empresa_id=empresa.id, name=name, codigo=code, es_base=True, is_active=True
            )
            self.session.add(role)
            await self.session.flush()
            roles[code] = role
            selected = (
                permissions
                if permission_codes is None
                else [
                    permission_by_code[code_]
                    for code_ in permission_codes
                    if code_ in permission_by_code
                ]
            )
            if selected:
                await self.session.execute(
                    rol_permiso_table.insert(),
                    [{"rol_id": role.id, "permiso_id": permission.id} for permission in selected],
                )

        admin = UserModel(
            empresa_id=empresa.id,
            name=admin_data["nombre"].strip(),
            apellido=admin_data["apellido"].strip(),
            email=email,
            username=username,
            hashed_password=self.password_hasher.hash(admin_data["password"]),
            telefono=admin_data.get("telefono"),
            is_active=True,
            email_verified=False,
            debe_cambiar_password=True,
        )
        self.session.add(admin)
        await self.session.flush()
        await self.session.execute(
            usuario_rol_table.insert().values(usuario_id=admin.id, rol_id=roles["ADMIN_EMPRESA"].id)
        )

        raw_token = secrets.token_urlsafe(32)
        from ssas.core.security.jwt import JWTService

        self.session.add(
            EmailVerificationTokenModel(
                id=str(uuid4()),
                empresa_id=empresa.id,
                user_id=admin.id,
                token_hash=JWTService().fingerprint(raw_token),
                expires_at=datetime.now(UTC)
                + timedelta(minutes=settings.app_email_verification_expire_minutes),
            )
        )
        await self.session.flush()
        empresa = await self.repository.get_empresa(empresa.id)
        return empresa, admin, raw_token
