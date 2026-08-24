from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from ssah.auth.infrastructure.persistence.models.password_reset_token import (  # noqa: F401
    PasswordResetTokenModel,
)
from ssah.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel  # noqa: F401
from ssah.auth.infrastructure.persistence.models.user import UserModel  # noqa: F401
from ssah.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel  # noqa: F401
from ssah.config.settings import settings
from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.permission import PermissionModel  # noqa: F401
from ssah.roles.infrastructure.persistence.models.role import RoleModel  # noqa: F401
from ssah.roles.infrastructure.persistence.models.role_permission import (  # noqa: F401
    RolePermissionModel,
)
from ssah.roles.infrastructure.persistence.models.user_role import UserRoleModel  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
