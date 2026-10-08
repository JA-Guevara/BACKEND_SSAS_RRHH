"""Crear tabla widget_panel para tarjetas del panel de reportes.

Revision ID: 20261008_0011
Revises: 20261008_0010
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20261008_0011"
down_revision = "20261008_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tablas = inspector.get_table_names()
    if "widget_panel" not in tablas:
        op.create_table(
            "widget_panel",
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
                nullable=False,
                index=True,
            ),
            sa.Column(
                "usuario_id",
                UUID(as_uuid=False),
                sa.ForeignKey("usuario.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("titulo", sa.String(120), nullable=False),
            sa.Column("tipo", sa.String(24), nullable=False),
            sa.Column("consulta", JSONB(), nullable=False),
            sa.Column("posicion", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ancho", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "fecha_registro",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "idx_widget_panel_empresa",
            "widget_panel",
            ["empresa_id", "usuario_id", "posicion"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tablas = inspector.get_table_names()
    if "widget_panel" in tablas:
        op.drop_index("idx_widget_panel_empresa", table_name="widget_panel")
        op.drop_table("widget_panel")
