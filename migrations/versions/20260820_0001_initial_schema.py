"""Create Sprint 0 multi-company security schema.

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260820_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TABLE empresa (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nit VARCHAR(30),
            razon_social VARCHAR(200) NOT NULL,
            nombre_comercial VARCHAR(200) NOT NULL,
            slug VARCHAR(120) NOT NULL UNIQUE,
            email VARCHAR(150),
            telefono VARCHAR(40),
            direccion TEXT,
            ciudad VARCHAR(100),
            logo_url TEXT,
            activo BOOLEAN NOT NULL DEFAULT true,
            fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_empresa_nit UNIQUE (nit),
            CONSTRAINT chk_empresa_slug_no_vacio CHECK (length(trim(slug)) > 0)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE plan_suscripcion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nombre VARCHAR(120) NOT NULL UNIQUE,
            precio_mensual NUMERIC(12, 2) NOT NULL DEFAULT 0,
            max_empleados INTEGER NOT NULL,
            modulos JSONB NOT NULL DEFAULT '[]'::jsonb,
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_plan_precio_no_negativo CHECK (precio_mensual >= 0),
            CONSTRAINT chk_plan_max_empleados_positivo CHECK (max_empleados > 0)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE suscripcion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            plan_id UUID NOT NULL REFERENCES plan_suscripcion(id) ON DELETE RESTRICT,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE,
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_suscripcion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
        )
        """
    )
    op.execute("CREATE INDEX idx_suscripcion_empresa_id ON suscripcion(empresa_id)")
    op.execute("CREATE INDEX idx_suscripcion_plan_id ON suscripcion(plan_id)")
    op.execute(
        """
        CREATE TABLE permiso (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            codigo VARCHAR(120) NOT NULL UNIQUE,
            modulo VARCHAR(80) NOT NULL,
            recurso VARCHAR(80) NOT NULL,
            operacion VARCHAR(80) NOT NULL,
            descripcion TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_permiso_modulo_recurso_operacion UNIQUE (modulo, recurso, operacion)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE rol (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            nombre VARCHAR(120) NOT NULL,
            codigo VARCHAR(80) NOT NULL,
            descripcion TEXT,
            es_base BOOLEAN NOT NULL DEFAULT false,
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_rol_empresa_codigo UNIQUE (empresa_id, codigo),
            CONSTRAINT uq_rol_empresa_nombre UNIQUE (empresa_id, nombre)
        )
        """
    )
    op.execute("CREATE INDEX idx_rol_empresa_id ON rol(empresa_id)")
    op.execute(
        """
        CREATE TABLE usuario (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            nombre VARCHAR(120) NOT NULL,
            apellido VARCHAR(120) NOT NULL DEFAULT '',
            email VARCHAR(150) NOT NULL,
            username VARCHAR(80) NOT NULL,
            password_hash TEXT NOT NULL,
            telefono VARCHAR(40),
            ultimo_acceso TIMESTAMPTZ,
            debe_cambiar_password BOOLEAN NOT NULL DEFAULT false,
            activo BOOLEAN NOT NULL DEFAULT true,
            email_verified BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_usuario_empresa_email UNIQUE (empresa_id, email),
            CONSTRAINT uq_usuario_empresa_username UNIQUE (empresa_id, username)
        )
        """
    )
    op.execute("CREATE INDEX idx_usuario_empresa_id ON usuario(empresa_id)")
    op.execute("CREATE INDEX idx_usuario_email ON usuario(email)")
    op.execute(
        """
        CREATE TABLE rol_permiso (
            rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
            permiso_id UUID NOT NULL REFERENCES permiso(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (rol_id, permiso_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_rol_permiso_rol_id ON rol_permiso(rol_id)")
    op.execute("CREATE INDEX idx_rol_permiso_permiso_id ON rol_permiso(permiso_id)")
    op.execute(
        """
        CREATE TABLE usuario_rol (
            usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
            rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
            asignado_por_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
            fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (usuario_id, rol_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_usuario_rol_usuario_id ON usuario_rol(usuario_id)")
    op.execute("CREATE INDEX idx_usuario_rol_rol_id ON usuario_rol(rol_id)")
    op.execute(
        """
        CREATE TABLE parametro_legal (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pais VARCHAR(80) NOT NULL DEFAULT 'Bolivia',
            codigo VARCHAR(100) NOT NULL,
            nombre VARCHAR(150) NOT NULL,
            descripcion TEXT,
            tipo_valor VARCHAR(50) NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_parametro_legal_pais_codigo UNIQUE (pais, codigo)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE parametro_valor (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            parametro_legal_id UUID NOT NULL REFERENCES parametro_legal(id) ON DELETE CASCADE,
            norma_legal VARCHAR(150),
            valor NUMERIC(14, 4) NOT NULL,
            vigente_desde DATE NOT NULL,
            vigente_hasta DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_parametro_valor_fechas CHECK (vigente_hasta IS NULL OR vigente_hasta >= vigente_desde)
        )
        """
    )
    op.execute("CREATE INDEX idx_parametro_valor_empresa_id ON parametro_valor(empresa_id)")
    op.execute("CREATE INDEX idx_parametro_valor_parametro_id ON parametro_valor(parametro_legal_id)")
    op.execute(
        """
        CREATE TABLE refresh_token (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_refresh_token_empresa_id ON refresh_token(empresa_id)")
    op.execute("CREATE INDEX idx_refresh_token_usuario_id ON refresh_token(usuario_id)")
    op.execute("CREATE INDEX idx_refresh_token_expires_at ON refresh_token(expires_at)")
    op.execute(
        """
        CREATE TABLE password_reset_token (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            consumed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_password_reset_token_empresa_id ON password_reset_token(empresa_id)")
    op.execute("CREATE INDEX idx_password_reset_token_usuario_id ON password_reset_token(usuario_id)")
    op.execute("CREATE INDEX idx_password_reset_token_expires_at ON password_reset_token(expires_at)")
    op.execute(
        """
        CREATE TABLE bitacora (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
            usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
            accion VARCHAR(100) NOT NULL,
            tabla_afectada VARCHAR(100),
            registro_id UUID,
            datos_previos_jsonb JSONB,
            datos_nuevos_jsonb JSONB,
            ip_origen INET,
            user_agent TEXT,
            fecha TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_bitacora_empresa_id ON bitacora(empresa_id)")
    op.execute("CREATE INDEX idx_bitacora_usuario_id ON bitacora(usuario_id)")
    op.execute("CREATE INDEX idx_bitacora_accion ON bitacora(accion)")
    op.execute("CREATE INDEX idx_bitacora_fecha ON bitacora(fecha)")

    for table in (
        "empresa",
        "plan_suscripcion",
        "suscripcion",
        "permiso",
        "rol",
        "usuario",
        "parametro_legal",
        "parametro_valor",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at()
            """
        )

def downgrade() -> None:
    for table in (
        "parametro_valor",
        "parametro_legal",
        "usuario",
        "rol",
        "permiso",
        "suscripcion",
        "plan_suscripcion",
        "empresa",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP TABLE IF EXISTS bitacora CASCADE")
    op.execute("DROP TABLE IF EXISTS password_reset_token CASCADE")
    op.execute("DROP TABLE IF EXISTS refresh_token CASCADE")
    op.execute("DROP TABLE IF EXISTS usuario_rol CASCADE")
    op.execute("DROP TABLE IF EXISTS rol_permiso CASCADE")
    op.execute("DROP TABLE IF EXISTS parametro_valor CASCADE")
    op.execute("DROP TABLE IF EXISTS parametro_legal CASCADE")
    op.execute("DROP TABLE IF EXISTS usuario CASCADE")
    op.execute("DROP TABLE IF EXISTS rol CASCADE")
    op.execute("DROP TABLE IF EXISTS permiso CASCADE")
    op.execute("DROP TABLE IF EXISTS suscripcion CASCADE")
    op.execute("DROP TABLE IF EXISTS plan_suscripcion CASCADE")
    op.execute("DROP TABLE IF EXISTS empresa CASCADE")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")