"""Add functional audit fields and case-insensitive tenant constraints.

Revision ID: 20260824_0002
Revises: 20260820_0001
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0002"
down_revision: str | None = "20260820_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bitacora", sa.Column("actor_etiqueta", sa.String(150), nullable=True))
    op.add_column("bitacora", sa.Column("modulo", sa.String(80), nullable=True))
    op.add_column(
        "bitacora",
        sa.Column("nivel", sa.String(16), nullable=False, server_default="INFO"),
    )
    op.add_column("bitacora", sa.Column("descripcion", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE bitacora
        SET modulo = 'LEGACY',
            descripcion = COALESCE(NULLIF(accion, ''), 'Evento migrado')
        WHERE modulo IS NULL OR descripcion IS NULL
        """
    )
    op.alter_column("bitacora", "modulo", nullable=False)
    op.alter_column("bitacora", "descripcion", nullable=False)
    op.create_index("idx_bitacora_modulo", "bitacora", ["modulo"])

    op.execute("CREATE UNIQUE INDEX uq_empresa_slug_ci ON empresa(lower(slug))")
    op.execute(
        "CREATE UNIQUE INDEX uq_rol_empresa_codigo_ci ON rol(empresa_id, lower(codigo))"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_rol_empresa_nombre_ci ON rol(empresa_id, lower(nombre))"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_usuario_empresa_email_ci ON usuario(empresa_id, lower(email))"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_usuario_empresa_username_ci "
        "ON usuario(empresa_id, lower(username))"
    )

    op.execute(
        """
        INSERT INTO plan_suscripcion (nombre, precio_mensual, max_empleados, modulos)
        VALUES (
            'Plan Inicial',
            0,
            50,
            '["usuarios", "roles", "bitacora", "parametros"]'::jsonb
        )
        ON CONFLICT (nombre) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO permiso (codigo, modulo, recurso, operacion, descripcion)
        VALUES
            ('usuarios:crear', 'USUARIOS', 'usuarios', 'crear', 'Crear usuarios de la empresa'),
            ('usuarios:editar', 'USUARIOS', 'usuarios', 'editar', 'Editar usuarios de la empresa'),
            ('roles:gestionar', 'ROLES', 'roles', 'gestionar', 'Gestionar roles y permisos'),
            ('bitacora:ver', 'BITACORA', 'bitacora', 'ver', 'Consultar la bitácora de la empresa'),
            ('parametros:ver', 'EMPRESAS', 'parametros', 'ver', 'Consultar parámetros de empresa'),
            ('parametros:editar', 'EMPRESAS', 'parametros', 'editar', 'Editar parámetros de empresa'),
            ('vacantes:gestionar', 'RECLUTAMIENTO', 'vacantes', 'gestionar', 'Gestionar vacantes'),
            ('candidatos:gestionar', 'RECLUTAMIENTO', 'candidatos', 'gestionar', 'Gestionar candidatos'),
            ('aprobaciones:gestionar', 'PERSONAL', 'aprobaciones', 'gestionar', 'Gestionar aprobaciones')
        ON CONFLICT (codigo) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO parametro_legal
            (pais, codigo, nombre, descripcion, tipo_valor)
        VALUES
            ('Bolivia', 'AFP_APORTE_LABORAL', 'Aporte laboral AFP',
             'Porcentaje de aporte laboral a la AFP', 'porcentaje'),
            ('Bolivia', 'APORTE_SOLIDARIO', 'Aporte solidario',
             'Porcentaje de aporte solidario aplicable', 'porcentaje'),
            ('Bolivia', 'RC_IVA', 'RC-IVA',
             'Porcentaje de retención del RC-IVA', 'porcentaje')
        ON CONFLICT (pais, codigo) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_usuario_empresa_username_ci")
    op.execute("DROP INDEX IF EXISTS uq_usuario_empresa_email_ci")
    op.execute("DROP INDEX IF EXISTS uq_rol_empresa_nombre_ci")
    op.execute("DROP INDEX IF EXISTS uq_rol_empresa_codigo_ci")
    op.execute("DROP INDEX IF EXISTS uq_empresa_slug_ci")
    op.drop_index("idx_bitacora_modulo", table_name="bitacora")
    op.drop_column("bitacora", "descripcion")
    op.drop_column("bitacora", "nivel")
    op.drop_column("bitacora", "modulo")
    op.drop_column("bitacora", "actor_etiqueta")
