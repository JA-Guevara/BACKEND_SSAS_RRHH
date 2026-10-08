"""Agregar foto_url a usuario e ip_origen / user_agent a refresh_token.

Revision ID: 20261008_0012
Revises: 20261008_0011
"""

import sqlalchemy as sa
from alembic import op

revision = "20261008_0012"
down_revision = "20261008_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # 1. Columna foto_url en usuario
    columnas_usuario = [c["name"] for c in inspector.get_columns("usuario")]
    if "foto_url" not in columnas_usuario:
        op.add_column("usuario", sa.Column("foto_url", sa.Text(), nullable=True))

    # 2. Columnas ip_origen y user_agent en refresh_token
    columnas_rt = [c["name"] for c in inspector.get_columns("refresh_token")]
    if "ip_origen" not in columnas_rt:
        op.add_column("refresh_token", sa.Column("ip_origen", sa.String(50), nullable=True))
    if "user_agent" not in columnas_rt:
        op.add_column("refresh_token", sa.Column("user_agent", sa.Text(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    columnas_usuario = [c["name"] for c in inspector.get_columns("usuario")]
    if "foto_url" in columnas_usuario:
        op.drop_column("usuario", "foto_url")

    columnas_rt = [c["name"] for c in inspector.get_columns("refresh_token")]
    if "user_agent" in columnas_rt:
        op.drop_column("refresh_token", "user_agent")
    if "ip_origen" in columnas_rt:
        op.drop_column("refresh_token", "ip_origen")
