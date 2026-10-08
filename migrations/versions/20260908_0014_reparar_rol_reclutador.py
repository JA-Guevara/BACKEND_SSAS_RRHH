"""Migración stub para enlazar la revisión histórica 20260908_0014.

Revision ID: 20260908_0014
Revises: None
"""

from collections.abc import Sequence

revision: str = "20260908_0014"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
