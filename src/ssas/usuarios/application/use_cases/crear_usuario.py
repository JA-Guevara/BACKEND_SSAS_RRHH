from ssas.auth.ports.outgoing.password_hasher import PasswordHasher
from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.domain.exceptions import (
    InvalidRoleForEmpresaError,
    UsuarioAlreadyExistsError,
    UsuarioWithoutRoleError,
)
from ssas.usuarios.ports.outgoing.usuario_repository import UsuarioRepository


class CrearUsuario:
    def __init__(self, usuario_repository: UsuarioRepository, password_hasher: PasswordHasher):
        self.usuario_repository = usuario_repository
        self.password_hasher = password_hasher

    async def execute(
        self,
        empresa_id: str,
        nombre: str,
        apellido: str,
        email: str,
        username: str,
        password: str,
        role_ids: list[str],
        telefono: str | None = None,
    ) -> Usuario:
        normalized_email = email.strip().lower()
        normalized_username = username.strip().lower()
        if not role_ids:
            raise UsuarioWithoutRoleError("El usuario debe tener al menos un rol asignado")
        if await self.usuario_repository.get_by_email(normalized_email, empresa_id):
            raise UsuarioAlreadyExistsError("Ya existe un usuario con ese email en la empresa")
        if await self.usuario_repository.get_by_username(normalized_username, empresa_id):
            raise UsuarioAlreadyExistsError("Ya existe un usuario con ese username en la empresa")
        if not await self.usuario_repository.role_ids_belong_to_empresa(role_ids, empresa_id):
            raise InvalidRoleForEmpresaError("Uno o más roles no pertenecen a la empresa")

        return await self.usuario_repository.create_usuario(
            empresa_id=empresa_id,
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            email=normalized_email,
            username=normalized_username,
            password_hash=self.password_hasher.hash(password),
            telefono=telefono.strip() if telefono else None,
            role_ids=role_ids,
        )