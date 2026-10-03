"""Preview and create company users without exposing imported passwords."""

import re

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from ssas.auth.domain.exceptions import AuthError, InvalidPasswordError
from ssas.auth.domain.password_policy import validate_password
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.importacion.application.catalogos import ImportErrorDetail, parse_file
from ssas.roles.infrastructure.persistence.models.role import RoleModel
from ssas.usuarios.application.use_cases.crear_usuario import CrearUsuario
from ssas.usuarios.domain.exceptions import UsuarioError
from ssas.usuarios.infrastructure.persistence.repositories.usuario_repository import (
    SqlAlchemyUsuarioRepository,
)

EMAIL = TypeAdapter(EmailStr)


async def preview_users(session, company_id: str, content: bytes, filename: str):
    digest, rows = parse_file("usuarios", content, filename)
    users = (await session.scalars(select(UserModel).where(UserModel.empresa_id == company_id))).all()
    roles = (await session.scalars(select(RoleModel).where(RoleModel.empresa_id == company_id))).all()
    emails = {user.email.casefold() for user in users}
    usernames = {user.username.casefold() for user in users}
    role_codes = {role.codigo.casefold(): role.id for role in roles if role.is_active}
    seen_emails: set[str] = set()
    seen_usernames: set[str] = set()
    result = []
    for number, row in enumerate(rows, 2):
        email = row["email"].casefold()
        username = row["username"].casefold()
        issues = []
        if not 2 <= len(row["nombre"]) <= 120 or not 1 <= len(row["apellido"]) <= 120:
            issues.append("Nombre o apellido inválido")
        if not re.fullmatch(r"[a-z0-9._-]{3,80}", username) or not 3 <= len(email) <= 150:
            issues.append("Usuario o correo inválido")
        try:
            EMAIL.validate_python(email)
        except ValidationError:
            issues.append("Correo inválido")
        if len(row["telefono"]) > 40:
            issues.append("Teléfono demasiado largo")
        if row["rol_codigo"].casefold() not in role_codes:
            issues.append("Rol inexistente o inactivo en esta empresa")
        try:
            validate_password(row["contrasena_inicial"], username, email)
        except InvalidPasswordError as exc:
            issues.append(str(exc))
        if email in emails or username in usernames:
            issues.append("Correo o usuario ya existe en esta empresa")
        if email in seen_emails or username in seen_usernames:
            issues.append("Correo o usuario repetido en el archivo")
        seen_emails.add(email)
        seen_usernames.add(username)
        safe_data = {key: value for key, value in row.items() if key != "contrasena_inicial"}
        result.append({"fila": number, "datos": safe_data,
                       "accion": "error" if issues else "crear", "errores": issues})
    return {
        "sha256": digest, "filas": result,
        "crear": sum(item["accion"] == "crear" for item in result),
        "omitir": 0, "errores": sum(item["accion"] == "error" for item in result),
    }


async def apply_users(session, company_id: str, content: bytes, filename: str, expected_digest: str):
    result = await preview_users(session, company_id, content, filename)
    if result["sha256"] != expected_digest:
        raise ImportErrorDetail("El archivo cambió desde la vista previa")
    if result["errores"]:
        raise ImportErrorDetail("Corrige las filas marcadas antes de importar")
    _, rows = parse_file("usuarios", content, filename)
    roles = (await session.scalars(select(RoleModel).where(RoleModel.empresa_id == company_id))).all()
    role_codes = {role.codigo.casefold(): role.id for role in roles if role.is_active}
    creator = CrearUsuario(SqlAlchemyUsuarioRepository(session), Argon2PasswordHasher())
    for row in rows:
        try:
            await creator.execute(
                empresa_id=company_id, nombre=row["nombre"], apellido=row["apellido"],
                email=row["email"], username=row["username"], password=row["contrasena_inicial"],
                role_ids=[role_codes[row["rol_codigo"].casefold()]],
                telefono=row["telefono"] or None, email_verificado=True,
            )
        except (UsuarioError, AuthError, KeyError) as exc:
            raise ImportErrorDetail("Los usuarios o roles cambiaron; vuelve a previsualizar") from exc
    return result
