"""Complete authentication security and user management.

Revision ID: 20260824_0003
Revises: 20260824_0002
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260824_0003"
down_revision: str | None = "20260824_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usuario",
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "usuario",
        sa.Column("ultimo_intento_fallido", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_usuario_intentos_fallidos_no_negativo",
        "usuario",
        "intentos_fallidos >= 0",
    )
    op.create_index("idx_usuario_bloqueado_hasta", "usuario", ["bloqueado_hasta"])

    # Las cuentas anteriores ya eran operativas; solo las nuevas requieren verificación.
    op.execute("UPDATE usuario SET email_verified = true")

    op.create_table(
        "email_verification_token",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_email_verification_token_usuario_id",
        "email_verification_token",
        ["usuario_id"],
    )
    op.create_index(
        "idx_email_verification_token_expires_at",
        "email_verification_token",
        ["expires_at"],
    )

    op.execute(
        """
        INSERT INTO permiso (codigo, modulo, recurso, operacion, descripcion)
        VALUES
            ('usuarios:ver', 'USUARIOS', 'usuarios', 'ver', 'Consultar usuarios de la empresa'),
            ('usuarios:cambiar_password', 'USUARIOS', 'usuarios', 'cambiar_password', 'Asignar contraseña temporal a usuarios'),
            ('usuarios:desbloquear', 'USUARIOS', 'usuarios', 'desbloquear', 'Desbloquear cuentas de usuario')
        ON CONFLICT (codigo) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT r.id, p.id
        FROM rol r
        CROSS JOIN permiso p
        WHERE r.codigo = 'ADMIN_EMPRESA'
          AND p.codigo IN ('usuarios:ver', 'usuarios:cambiar_password', 'usuarios:desbloquear')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rol_permiso
        WHERE permiso_id IN (
            SELECT id FROM permiso
            WHERE codigo IN ('usuarios:ver', 'usuarios:cambiar_password', 'usuarios:desbloquear')
        )
        """
    )
    op.execute(
        "DELETE FROM permiso WHERE codigo IN "
        "('usuarios:ver', 'usuarios:cambiar_password', 'usuarios:desbloquear')"
    )
    op.drop_index(
        "idx_email_verification_token_expires_at",
        table_name="email_verification_token",
    )
    op.drop_index(
        "idx_email_verification_token_usuario_id",
        table_name="email_verification_token",
    )
    op.drop_table("email_verification_token")
    op.drop_index("idx_usuario_bloqueado_hasta", table_name="usuario")
    op.drop_constraint(
        "ck_usuario_intentos_fallidos_no_negativo", "usuario", type_="check"
    )
    op.drop_column("usuario", "ultimo_intento_fallido")
    op.drop_column("usuario", "bloqueado_hasta")
    op.drop_column("usuario", "intentos_fallidos")
