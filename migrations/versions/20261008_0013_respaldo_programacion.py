"""Agregar tabla respaldo_programacion y columna programacion_id en respaldo.

Revision ID: 20261008_0013
Revises: 20261008_0012
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20261008_0013"
down_revision = "20261008_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = inspector.get_table_names()

    if "respaldo_programacion" not in tables:
        op.create_table(
            "respaldo_programacion",
            sa.Column(
                "id",
                UUID(as_uuid=False),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "empresa_id",
                UUID(as_uuid=False),
                sa.ForeignKey("empresa.id", ondelete="CASCADE"),
                nullable=True,
                index=True,
            ),
            sa.Column("nombre", sa.String(120), nullable=False),
            sa.Column("frecuencia", sa.String(20), nullable=False),
            sa.Column("hora", sa.String(8), nullable=False),
            sa.Column("dia_semana", sa.SmallInteger(), nullable=True),
            sa.Column("dia_mes", sa.SmallInteger(), nullable=True),
            sa.Column(
                "retencion_dias",
                sa.SmallInteger(),
                nullable=False,
                server_default=sa.text("30"),
            ),
            sa.Column(
                "activo", sa.Boolean(), nullable=False, server_default=sa.text("true")
            ),
            sa.Column("ultima_ejecucion", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "proxima_ejecucion",
                sa.DateTime(timezone=True),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "creado_por_id",
                UUID(as_uuid=False),
                sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "fecha_creacion",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    columnas_respaldo = [c["name"] for c in inspector.get_columns("respaldo")]
    if "programacion_id" not in columnas_respaldo:
        op.add_column(
            "respaldo",
            sa.Column(
                "programacion_id",
                UUID(as_uuid=False),
                sa.ForeignKey("respaldo_programacion.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    op.drop_column("respaldo", "programacion_id")
    op.drop_table("respaldo_programacion")
