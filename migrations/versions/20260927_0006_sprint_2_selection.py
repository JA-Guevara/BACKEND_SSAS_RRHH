"""Sprint 2 selection schema and system-role grants.

Revision ID: 20260927_0006
Revises: 20260915_0005

Downgrade destroys Sprint 2 history. Use only on a disposable database.
Existing invalid empleado_id references abort upgrade; they are never cleared.
"""

from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260927_0006"
down_revision = "20260915_0005"
branch_labels = None
depends_on = None

TENANT_PERMISSIONS = [
    "entrevistas:ver",
    "entrevistas:gestionar",
    "entrevistas:registrar_resultado",
    "evaluaciones:ver",
    "evaluaciones:gestionar",
    "postulaciones:analizar_cv",
    "postulaciones:contratar",
    "empleados:ver",
]
PERMISSIONS = (
    *TENANT_PERMISSIONS,
    *(f"platform:{code}" for code in TENANT_PERMISSIONS),
    "platform:postulantes:gestionar",
)
ROLE_GRANTS = {
    "ADMIN_EMPRESA": TENANT_PERMISSIONS,
    "RRHH": [
        "vacantes:ver",
        "habilidades:ver",
        "postulantes:ver",
        "postulantes:gestionar",
        "postulaciones:ver",
        "postulaciones:gestionar",
        "entrevistas:ver",
        "entrevistas:gestionar",
        "entrevistas:registrar_resultado",
        "evaluaciones:ver",
        "evaluaciones:gestionar",
        "postulaciones:analizar_cv",
        "postulaciones:contratar",
        "empleados:ver",
    ],
    "RECLUTADOR": [
        "entrevistas:ver",
        "entrevistas:gestionar",
        "entrevistas:registrar_resultado",
        "evaluaciones:ver",
        "evaluaciones:gestionar",
        "postulaciones:analizar_cv",
        "postulantes:gestionar",
    ],
    "JEFE_AREA": [
        "entrevistas:ver",
        "entrevistas:registrar_resultado",
        "evaluaciones:ver",
        "evaluaciones:gestionar",
    ],
}
PERMISSION_NAMESPACE = UUID("b065ee90-6f1b-4c43-8850-d759ee06f531")


def upgrade() -> None:
    op.create_table(
        "entrevista",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("postulacion_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("entrevistador_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracion_min", sa.Integer(), nullable=False),
        sa.Column("modalidad", sa.String(20), nullable=False),
        sa.Column("enlace_reunion", sa.Text(), nullable=True),
        sa.Column("lugar", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'PROGRAMADA'")),
        sa.Column("puntaje", sa.Numeric(5, 2), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("recomendacion", sa.String(40), nullable=True),
        sa.Column(
            "fecha_registro",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["postulacion_id"], ["postulacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entrevistador_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("duracion_min > 0", name="ck_entrevista_duracion"),
        sa.CheckConstraint(
            "puntaje IS NULL OR (puntaje >= 0 AND puntaje <= 100)", name="ck_entrevista_puntaje"
        ),
        sa.CheckConstraint(
            "estado IN ('PROGRAMADA', 'CONFIRMADA', 'REALIZADA', 'CANCELADA')",
            name="ck_entrevista_estado",
        ),
        sa.CheckConstraint(
            "modalidad IN ('VIRTUAL', 'PRESENCIAL', 'TELEFONICA')", name="ck_entrevista_modalidad"
        ),
        sa.CheckConstraint(
            "(modalidad = 'VIRTUAL' AND enlace_reunion IS NOT NULL AND length(trim(enlace_reunion)) > 0) OR (modalidad = 'PRESENCIAL' AND lugar IS NOT NULL AND length(trim(lugar)) > 0) OR modalidad = 'TELEFONICA'",
            name="ck_entrevista_ubicacion",
        ),
    )
    op.create_index("idx_entrevista_postulacion_id", "entrevista", ["postulacion_id"])
    op.create_index(
        "idx_entrevista_entrevistador_id_fecha_hora",
        "entrevista",
        ["entrevistador_id", "fecha_hora"],
    )
    op.create_index("idx_entrevista_fecha_hora", "entrevista", ["fecha_hora"])
    op.create_index("idx_entrevista_estado", "entrevista", ["estado"])
    op.create_table(
        "evaluacion",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("postulacion_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("evaluador_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("puntaje", sa.Numeric(10, 2), nullable=False),
        sa.Column("puntaje_maximo", sa.Numeric(10, 2), nullable=False),
        sa.Column("aprobado", sa.Boolean(), nullable=False),
        sa.Column("archivo_url", sa.Text(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["postulacion_id"], ["postulacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluador_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "puntaje_maximo > 0 AND puntaje >= 0 AND puntaje <= puntaje_maximo",
            name="ck_evaluacion_puntaje",
        ),
    )
    op.create_index(
        "idx_evaluacion_postulacion_id_fecha", "evaluacion", ["postulacion_id", "fecha"]
    )
    op.create_index("idx_evaluacion_evaluador_id", "evaluacion", ["evaluador_id"])
    op.create_index("idx_evaluacion_fecha", "evaluacion", ["fecha"])
    op.create_table(
        "analisis_cv",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("postulacion_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("puntaje_afinidad", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "habilidades_detectadas",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "habilidades_faltantes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("anios_experiencia_detectados", sa.Numeric(5, 2), nullable=True),
        sa.Column("resumen_ia", sa.Text(), nullable=False),
        sa.Column(
            "fortalezas", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("modelo_usado", sa.String(120), nullable=False),
        sa.Column("tiempo_proceso_ms", sa.Integer(), nullable=False),
        sa.Column(
            "fecha_analisis",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["postulacion_id"], ["postulacion.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "puntaje_afinidad >= 0 AND puntaje_afinidad <= 100", name="ck_analisis_cv_afinidad"
        ),
        sa.CheckConstraint(
            "anios_experiencia_detectados IS NULL OR anios_experiencia_detectados >= 0",
            name="ck_analisis_cv_experiencia",
        ),
        sa.CheckConstraint("tiempo_proceso_ms >= 0", name="ck_analisis_cv_tiempo"),
        sa.CheckConstraint(
            "jsonb_typeof(habilidades_detectadas) = 'array'",
            name="ck_analisis_cv_habilidades_detectadas",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(habilidades_faltantes) = 'array'",
            name="ck_analisis_cv_habilidades_faltantes",
        ),
        sa.CheckConstraint("jsonb_typeof(fortalezas) = 'array'", name="ck_analisis_cv_fortalezas"),
    )
    op.create_index(
        "idx_analisis_cv_postulacion_id_fecha_analisis",
        "analisis_cv",
        ["postulacion_id", "fecha_analisis"],
    )
    op.create_index("idx_analisis_cv_fecha_analisis", "analisis_cv", ["fecha_analisis"])
    op.create_table(
        "postulante_habilidad",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("postulante_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("habilidad_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("nivel", sa.String(30), nullable=True),
        sa.Column(
            "anios_experiencia", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "detectado_por_ia", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["postulante_id"], ["postulante.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["habilidad_id"], ["habilidad.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("anios_experiencia >= 0", name="ck_postulante_habilidad_experiencia"),
        sa.UniqueConstraint(
            "postulante_id", "habilidad_id", name="uq_postulante_habilidad_postulante_habilidad"
        ),
    )
    op.create_index(
        "idx_postulante_habilidad_postulante_id", "postulante_habilidad", ["postulante_id"]
    )
    op.create_index(
        "idx_postulante_habilidad_habilidad_id", "postulante_habilidad", ["habilidad_id"]
    )
    op.create_table(
        "empleado",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("empresa_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("usuario_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombres", sa.String(120), nullable=False),
        sa.Column("apellido_paterno", sa.String(120), nullable=False),
        sa.Column("apellido_materno", sa.String(120), nullable=True),
        sa.Column("ci", sa.String(30), nullable=False),
        sa.Column("ci_expedido", sa.String(10), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("genero", sa.String(20), nullable=True),
        sa.Column("estado_civil", sa.String(30), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("email_personal", sa.String(150), nullable=True),
        sa.Column("contacto_emergencia", sa.String(200), nullable=True),
        sa.Column("telefono_emergencia", sa.String(40), nullable=True),
        sa.Column("nua_cua", sa.String(40), nullable=True),
        sa.Column("afp", sa.String(80), nullable=True),
        sa.Column("banco", sa.String(120), nullable=True),
        sa.Column("numero_cuenta", sa.String(80), nullable=True),
        sa.Column("tipo_cuenta", sa.String(40), nullable=True),
        sa.Column("fecha_ingreso", sa.Date(), nullable=False),
        sa.Column("fecha_salida", sa.Date(), nullable=True),
        sa.Column("motivo_salida", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'ACTIVO'")),
        sa.Column("foto_url", sa.Text(), nullable=True),
        sa.Column(
            "fecha_registro",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "fecha_salida IS NULL OR fecha_salida >= fecha_ingreso", name="ck_empleado_fechas"
        ),
        sa.CheckConstraint("estado IN ('ACTIVO', 'INACTIVO')", name="ck_empleado_estado"),
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_empleado_empresa_codigo"),
        sa.UniqueConstraint("empresa_id", "ci", name="uq_empleado_empresa_ci"),
    )
    op.create_index("idx_empleado_empresa_id", "empleado", ["empresa_id"])
    op.create_index("idx_empleado_usuario_id", "empleado", ["usuario_id"])
    op.create_index("idx_empleado_empresa_id_estado", "empleado", ["empresa_id", "estado"])
    op.create_index("idx_empleado_fecha_ingreso", "empleado", ["fecha_ingreso"])
    op.create_index(
        "uq_empleado_empresa_codigo_ci",
        "empleado",
        ["empresa_id", sa.text("lower(codigo)")],
        unique=True,
    )
    op.create_index(
        "uq_empleado_empresa_ci_ci", "empleado", ["empresa_id", sa.text("lower(ci)")], unique=True
    )

    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM postulacion p LEFT JOIN empleado e ON e.id = p.empleado_id
                WHERE p.empleado_id IS NOT NULL AND e.id IS NULL
            ) THEN
                RAISE EXCEPTION 'Invalid postulacion.empleado_id references; resolve explicitly before Sprint 2 migration';
            END IF;
        END $$
    """)
    op.create_foreign_key(
        "fk_postulacion_empleado_id",
        "postulacion",
        "empleado",
        ["empleado_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    for code in PERMISSIONS:
        resource, action = code.split(":")[-2:]
        module = "PLATFORM" if code.startswith("platform:") else "RECLUTAMIENTO"
        permission_id = str(uuid5(PERMISSION_NAMESPACE, code))
        op.execute(
            sa.text(
                "INSERT INTO permiso (id, codigo, modulo, recurso, operacion, descripcion) "
                f"VALUES ('{permission_id}', '{code}', '{module}', '{resource}', '{action}', '{code}') "
                "ON CONFLICT (codigo) DO NOTHING"
            )
        )
    # Only system roles receive grants; custom roles and existing grants are preserved.
    for role, codes in ROLE_GRANTS.items():
        values = ", ".join(f"'{code}'" for code in codes)
        op.execute(
            sa.text(
                "INSERT INTO rol_permiso (rol_id, permiso_id) "
                "SELECT r.id, p.id FROM rol r CROSS JOIN permiso p "
                f"WHERE r.es_sistema = TRUE AND r.empresa_id IS NOT NULL AND r.codigo = '{role}' "
                f"AND p.codigo IN ({values}) ON CONFLICT DO NOTHING"
            )
        )
    values = ", ".join(f"'{code}'" for code in PERMISSIONS if code.startswith("platform:"))
    op.execute(
        sa.text(
            "INSERT INTO rol_permiso (rol_id, permiso_id) "
            "SELECT r.id, p.id FROM rol r CROSS JOIN permiso p "
            "WHERE r.es_sistema = TRUE AND r.empresa_id IS NULL AND r.codigo = 'SUPER_ADMIN' "
            f"AND p.codigo IN ({values}) ON CONFLICT DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_postulacion_empleado_id", "postulacion", type_="foreignkey")
    for table in ("empleado", "postulante_habilidad", "analisis_cv", "evaluacion", "entrevista"):
        op.drop_table(table)
    # Leave any pre-existing permission with another ID intact.
    for code in PERMISSIONS:
        permission_id = str(uuid5(PERMISSION_NAMESPACE, code))
        op.execute(
            sa.text(f"DELETE FROM permiso WHERE codigo = '{code}' AND id = '{permission_id}'")
        )
