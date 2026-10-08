"""Registrar las columnas sensibles incluidas en cada reporte ejecutado.

Revision ID: 20261008_0010
Revises: 20261005_0009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261008_0010"
down_revision = "20261005_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columnas = {column["name"] for column in inspector.get_columns("reporte_ejecucion")}
    if "columnas_sensibles" not in columnas:
        op.add_column(
            "reporte_ejecucion",
            sa.Column(
                "columnas_sensibles",
                JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columnas = {column["name"] for column in inspector.get_columns("reporte_ejecucion")}
    if "columnas_sensibles" in columnas:
        op.drop_column("reporte_ejecucion", "columnas_sensibles")