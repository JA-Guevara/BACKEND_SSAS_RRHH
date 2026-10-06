"""Base de conocimiento por empresa para el chatbot.

Revision ID: 20261005_0009
Revises: 20261003_0008
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20261005_0009"
down_revision = "20261003_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conocimiento_articulo",
        sa.Column(
            "id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("empresa_id", UUID(as_uuid=False), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("titulo", sa.String(160), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("categoria", sa.String(80), nullable=False, server_default="General"),
        sa.Column("publico", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("publicado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_conocimiento_articulo_empresa", "conocimiento_articulo", ["empresa_id"])
    op.create_table(
        "conocimiento_fragmento",
        sa.Column(
            "id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "articulo_id",
            UUID(as_uuid=False),
            sa.ForeignKey("conocimiento_articulo.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("empresa_id", UUID(as_uuid=False), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("vector", JSONB(), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False),
    )
    op.create_index("ix_conocimiento_fragmento_empresa", "conocimiento_fragmento", ["empresa_id"])


def downgrade() -> None:
    op.drop_table("conocimiento_fragmento")
    op.drop_table("conocimiento_articulo")
