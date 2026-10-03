"""Permission for tenant-scoped catalog import.

Revision ID: 20261002_0007
Revises: 20260927_0006
"""

from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision = "20261002_0007"
down_revision = "20260927_0006"
branch_labels = None
depends_on = None

NAMESPACE = UUID("b065ee90-6f1b-4c43-8850-d759ee06f531")


def upgrade() -> None:
    for code, module in (("importacion:gestionar", "ORGANIZACION"),
                         ("platform:importacion:gestionar", "PLATFORM")):
        permission_id = str(uuid5(NAMESPACE, code))
        op.execute(sa.text(
            "INSERT INTO permiso (id, codigo, modulo, recurso, operacion, descripcion) "
            f"VALUES ('{permission_id}', '{code}', '{module}', 'importacion', 'gestionar', '{code}') "
            "ON CONFLICT (codigo) DO NOTHING"
        ))
        role_code = "SUPER_ADMIN" if code.startswith("platform:") else "ADMIN_EMPRESA"
        scope = "IS NULL" if code.startswith("platform:") else "IS NOT NULL"
        op.execute(sa.text(
            "INSERT INTO rol_permiso (rol_id, permiso_id) "
            "SELECT r.id, p.id FROM rol r CROSS JOIN permiso p "
            f"WHERE r.es_sistema = TRUE AND r.empresa_id {scope} "
            f"AND r.codigo = '{role_code}' AND p.codigo = '{code}' "
            "ON CONFLICT DO NOTHING"
        ))


def downgrade() -> None:
    for code in ("importacion:gestionar", "platform:importacion:gestionar"):
        permission_id = str(uuid5(NAMESPACE, code))
        op.execute(sa.text(f"DELETE FROM permiso WHERE codigo = '{code}' AND id = '{permission_id}'"))
