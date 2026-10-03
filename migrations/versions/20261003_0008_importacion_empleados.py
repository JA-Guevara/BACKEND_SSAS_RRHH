"""Permission to bulk import employee records.

Revision ID: 20261003_0008
Revises: 20261002_0007
"""

from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision = "20261003_0008"
down_revision = "20261002_0007"
branch_labels = None
depends_on = None

NAMESPACE = UUID("b065ee90-6f1b-4c43-8850-d759ee06f531")
PERMISSIONS = (
    ("empleados:importar", "ORGANIZACION", "ADMIN_EMPRESA", "IS NOT NULL"),
    ("platform:empleados:importar", "PLATFORM", "SUPER_ADMIN", "IS NULL"),
)


def upgrade() -> None:
    for code, module, role, scope in PERMISSIONS:
        permission_id = str(uuid5(NAMESPACE, code))
        op.execute(sa.text(
            "INSERT INTO permiso (id, codigo, modulo, recurso, operacion, descripcion) "
            f"VALUES ('{permission_id}', '{code}', '{module}', 'empleados', 'importar', '{code}') "
            "ON CONFLICT (codigo) DO NOTHING"
        ))
        op.execute(sa.text(
            "INSERT INTO rol_permiso (rol_id, permiso_id) "
            "SELECT r.id, p.id FROM rol r CROSS JOIN permiso p "
            f"WHERE r.es_sistema = TRUE AND r.empresa_id {scope} "
            f"AND r.codigo = '{role}' AND p.codigo = '{code}' "
            "ON CONFLICT DO NOTHING"
        ))


def downgrade() -> None:
    for code, _, _, _ in PERMISSIONS:
        permission_id = str(uuid5(NAMESPACE, code))
        op.execute(sa.text(f"DELETE FROM permiso WHERE codigo = '{code}' AND id = '{permission_id}'"))
