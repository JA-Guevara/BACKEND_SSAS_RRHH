import argparse
import asyncio
import getpass
import sys

from ssas.auth.domain.exceptions import InvalidPasswordError
from ssas.auth.domain.password_policy import validate_password
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.infrastructure.database.session import AsyncSessionLocal
from ssas.platform.infrastructure.persistence.repositories.platform_repository import (
    PlatformRepository,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crea el primer superadministrador de SSAS")
    parser.add_argument("--nombre")
    parser.add_argument("--apellido")
    parser.add_argument("--email")
    parser.add_argument("--username")
    return parser


async def _create(args: argparse.Namespace, password: str) -> None:
    email = args.email.strip().lower()
    username = args.username.strip().lower()
    validate_password(password, email, username)
    async with AsyncSessionLocal() as session:
        repository = PlatformRepository(session)
        if await repository.get_admin_by_login(email) or await repository.get_admin_by_login(username):
            raise ValueError("Ya existe un administrador con ese email o username")
        admin = await repository.create_admin(
            nombre=args.nombre.strip(),
            apellido=args.apellido.strip(),
            email=email,
            username=username,
            password_hash=Argon2PasswordHasher().hash(password),
            activo=True,
            email_verified=True,
        )
        await repository.add_audit(
            admin_id=admin.id,
            actor_etiqueta=admin.email,
            modulo="AUTH_PLATFORM",
            accion="BOOTSTRAP",
            nivel="INFO",
            descripcion="Superadministrador inicial creado mediante CLI",
            tabla_afectada="administrador_plataforma",
            registro_id=admin.id,
        )
        await session.commit()
        print(f"Superadministrador creado: {admin.email} ({admin.id})")


def main() -> None:
    args = _parser().parse_args()
    args.nombre = args.nombre or input("Nombre: ").strip()
    args.apellido = args.apellido or input("Apellido: ").strip()
    args.email = args.email or input("Email: ").strip()
    args.username = args.username or input("Username: ").strip()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirmar password: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden")
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(_create(args, password))
    except (InvalidPasswordError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
