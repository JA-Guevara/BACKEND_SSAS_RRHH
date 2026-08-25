"""Add global platform administration.

Revision ID: 20260825_0004
Revises: 20260824_0003
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260825_0004"
down_revision: str | None = "20260824_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "administrador_plataforma",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("apellido", sa.String(120), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_intento_fallido", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("intentos_fallidos >= 0", name="ck_admin_plataforma_intentos_no_negativo"),
    )
    op.create_index("uq_admin_plataforma_email_ci", "administrador_plataforma", [sa.text("lower(email)")], unique=True)
    op.create_index("uq_admin_plataforma_username_ci", "administrador_plataforma", [sa.text("lower(username)")], unique=True)
    op.create_index("idx_admin_plataforma_bloqueado_hasta", "administrador_plataforma", ["bloqueado_hasta"])
    op.execute(
        """
        CREATE TRIGGER trg_administrador_plataforma_updated_at
        BEFORE UPDATE ON administrador_plataforma
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    )

    op.create_table(
        "platform_refresh_token",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("admin_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("administrador_plataforma.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_platform_refresh_admin_id", "platform_refresh_token", ["admin_id"])
    op.create_index("idx_platform_refresh_expires_at", "platform_refresh_token", ["expires_at"])

    op.create_table(
        "bitacora_plataforma",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("administrador_plataforma.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_etiqueta", sa.String(150), nullable=True),
        sa.Column("modulo", sa.String(80), nullable=False),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("nivel", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("tabla_afectada", sa.String(100), nullable=True),
        sa.Column("registro_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("datos_previos", postgresql.JSONB(), nullable=True),
        sa.Column("datos_nuevos", postgresql.JSONB(), nullable=True),
        sa.Column("ip_origen", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_bitacora_plataforma_admin_id", "bitacora_plataforma", ["admin_id"])
    op.create_index("idx_bitacora_plataforma_modulo", "bitacora_plataforma", ["modulo"])
    op.create_index("idx_bitacora_plataforma_fecha", "bitacora_plataforma", ["fecha"])

    op.execute(
        """
        INSERT INTO permiso (codigo, modulo, recurso, operacion, descripcion)
        VALUES
            ('empresa:ver', 'EMPRESAS', 'empresa', 'ver', 'Consultar la configuración de la propia empresa'),
            ('empresa:editar', 'EMPRESAS', 'empresa', 'editar', 'Editar la configuración permitida de la propia empresa')
        ON CONFLICT (codigo) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT r.id, p.id
        FROM rol r CROSS JOIN permiso p
        WHERE r.codigo = 'ADMIN_EMPRESA'
          AND p.codigo IN ('empresa:ver', 'empresa:editar')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rol_permiso WHERE permiso_id IN (
            SELECT id FROM permiso WHERE codigo IN ('empresa:ver', 'empresa:editar')
        )
        """
    )
    op.execute("DELETE FROM permiso WHERE codigo IN ('empresa:ver', 'empresa:editar')")
    op.drop_index("idx_bitacora_plataforma_fecha", table_name="bitacora_plataforma")
    op.drop_index("idx_bitacora_plataforma_modulo", table_name="bitacora_plataforma")
    op.drop_index("idx_bitacora_plataforma_admin_id", table_name="bitacora_plataforma")
    op.drop_table("bitacora_plataforma")
    op.drop_index("idx_platform_refresh_expires_at", table_name="platform_refresh_token")
    op.drop_index("idx_platform_refresh_admin_id", table_name="platform_refresh_token")
    op.drop_table("platform_refresh_token")
    op.execute("DROP TRIGGER IF EXISTS trg_administrador_plataforma_updated_at ON administrador_plataforma")
    op.drop_index("idx_admin_plataforma_bloqueado_hasta", table_name="administrador_plataforma")
    op.drop_index("uq_admin_plataforma_username_ci", table_name="administrador_plataforma")
    op.drop_index("uq_admin_plataforma_email_ci", table_name="administrador_plataforma")
    op.drop_table("administrador_plataforma")
