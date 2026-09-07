-- ============================================================
-- SSAH RRHH - Esquema PostgreSQL Sprint 0 + Sprint 1
-- ============================================================
-- Script de referencia para una base de datos nueva.
-- No contiene DROP, DELETE, TRUNCATE ni datos seed.
-- No ejecutar sobre una BD ya administrada por Alembic sin revisarlo.
--
-- Decisiones:
-- - empresa es el tenant del sistema.
-- - permiso es global; rol puede ser global (empresa_id NULL).
-- - postulante pertenece a empresa.
-- - empleado_id queda nullable y sin FK hasta crear tabla empleado.
-- - codigo_seguimiento se agrega a postulacion para soportar T1-08.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE plan_suscripcion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(120) NOT NULL UNIQUE,
    precio_mensual NUMERIC(12, 2) NOT NULL DEFAULT 0,
    max_empleados INTEGER NOT NULL,
    modulos JSONB NOT NULL DEFAULT '{}'::jsonb,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_plan_precio_no_negativo CHECK (precio_mensual >= 0),
    CONSTRAINT ck_plan_max_empleados_positivo CHECK (max_empleados > 0)
);

CREATE TABLE empresa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nit VARCHAR(30) UNIQUE,
    slug VARCHAR(120) NOT NULL UNIQUE,
    razon_social VARCHAR(200) NOT NULL,
    nombre_comercial VARCHAR(200) NOT NULL,
    direccion TEXT,
    ciudad VARCHAR(100),
    telefono VARCHAR(40),
    email VARCHAR(150),
    logo_url TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_empresa_slug_no_vacio CHECK (btrim(slug) <> '')
);

CREATE UNIQUE INDEX uq_empresa_slug_lower ON empresa (lower(slug));

CREATE TABLE suscripcion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plan_suscripcion(id) ON DELETE RESTRICT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_suscripcion_estado CHECK (
        estado IN ('ACTIVA', 'SUSPENDIDA', 'VENCIDA', 'CANCELADA')
    ),
    CONSTRAINT ck_suscripcion_fechas CHECK (
        fecha_fin IS NULL OR fecha_fin >= fecha_inicio
    )
);

CREATE INDEX ix_suscripcion_empresa_id ON suscripcion (empresa_id);
CREATE INDEX ix_suscripcion_plan_id ON suscripcion (plan_id);
CREATE INDEX ix_suscripcion_estado ON suscripcion (estado);

CREATE TABLE permiso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(120) NOT NULL UNIQUE,
    modulo VARCHAR(80) NOT NULL,
    recurso VARCHAR(80) NOT NULL,
    operacion VARCHAR(80) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_permiso_modulo_recurso_operacion
        UNIQUE (modulo, recurso, operacion)
);

CREATE TABLE rol (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    codigo VARCHAR(80) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    es_base BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_rol_empresa_codigo UNIQUE (empresa_id, codigo),
    CONSTRAINT uq_rol_empresa_nombre UNIQUE (empresa_id, nombre)
);

CREATE INDEX ix_rol_empresa_id ON rol (empresa_id);
CREATE UNIQUE INDEX uq_rol_empresa_codigo_lower
    ON rol (empresa_id, lower(codigo)) WHERE empresa_id IS NOT NULL;
CREATE UNIQUE INDEX uq_rol_empresa_nombre_lower
    ON rol (empresa_id, lower(nombre)) WHERE empresa_id IS NOT NULL;
CREATE UNIQUE INDEX uq_rol_global_codigo_lower
    ON rol (lower(codigo)) WHERE empresa_id IS NULL;
CREATE UNIQUE INDEX uq_rol_global_nombre_lower
    ON rol (lower(nombre)) WHERE empresa_id IS NULL;

CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash TEXT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    apellido VARCHAR(120) NOT NULL DEFAULT '',
    telefono VARCHAR(40),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    debe_cambiar_password BOOLEAN NOT NULL DEFAULT FALSE,
    ultimo_acceso TIMESTAMPTZ,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    ultimo_intento_fallido TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_usuario_empresa_username UNIQUE (empresa_id, username),
    CONSTRAINT uq_usuario_empresa_email UNIQUE (empresa_id, email),
    CONSTRAINT ck_usuario_intentos_fallidos CHECK (intentos_fallidos >= 0)
);

CREATE INDEX ix_usuario_empresa_id ON usuario (empresa_id);
CREATE UNIQUE INDEX uq_usuario_empresa_username_lower
    ON usuario (empresa_id, lower(username)) WHERE empresa_id IS NOT NULL;
CREATE UNIQUE INDEX uq_usuario_empresa_email_lower
    ON usuario (empresa_id, lower(email)) WHERE empresa_id IS NOT NULL;
CREATE UNIQUE INDEX uq_usuario_global_username_lower
    ON usuario (lower(username)) WHERE empresa_id IS NULL;
CREATE UNIQUE INDEX uq_usuario_global_email_lower
    ON usuario (lower(email)) WHERE empresa_id IS NULL;

CREATE TABLE rol_permiso (
    rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    permiso_id UUID NOT NULL REFERENCES permiso(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (rol_id, permiso_id)
);

CREATE TABLE usuario_rol (
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    asignado_por_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
    fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (usuario_id, rol_id)
);

CREATE INDEX ix_usuario_rol_rol_id ON usuario_rol (rol_id);

CREATE TABLE parametro_legal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(80) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    tipo_valor VARCHAR(30) NOT NULL,
    pais VARCHAR(80) NOT NULL DEFAULT 'Bolivia',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE parametro_valor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    parametro_id UUID NOT NULL REFERENCES parametro_legal(id) ON DELETE RESTRICT,
    valor NUMERIC(18, 6) NOT NULL,
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    norma_legal TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_parametro_valor_periodo
        UNIQUE (empresa_id, parametro_id, vigente_desde),
    CONSTRAINT ck_parametro_valor_fechas CHECK (
        vigente_hasta IS NULL OR vigente_hasta >= vigente_desde
    )
);

CREATE INDEX ix_parametro_valor_empresa_id ON parametro_valor (empresa_id);
CREATE INDEX ix_parametro_valor_parametro_id ON parametro_valor (parametro_id);

CREATE TABLE refresh_token (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_refresh_token_empresa_id ON refresh_token (empresa_id);
CREATE INDEX ix_refresh_token_usuario_id ON refresh_token (usuario_id);
CREATE INDEX ix_refresh_token_expires_at ON refresh_token (expires_at);

CREATE TABLE password_reset_token (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_password_reset_empresa_id ON password_reset_token (empresa_id);
CREATE INDEX ix_password_reset_usuario_id ON password_reset_token (usuario_id);
CREATE INDEX ix_password_reset_expires_at ON password_reset_token (expires_at);

CREATE TABLE email_verification_token (
    id UUID PRIMARY KEY,
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_email_verification_usuario_id
    ON email_verification_token (usuario_id);
CREATE INDEX ix_email_verification_expires_at
    ON email_verification_token (expires_at);

CREATE TABLE bitacora (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
    actor_etiqueta VARCHAR(150),
    modulo VARCHAR(80) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    nivel VARCHAR(16) NOT NULL DEFAULT 'INFO',
    descripcion TEXT NOT NULL,
    tabla_afectada VARCHAR(100),
    registro_id UUID,
    datos_previos_jsonb JSONB,
    datos_nuevos_jsonb JSONB,
    ip_origen INET,
    user_agent TEXT,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_bitacora_nivel CHECK (
        nivel IN ('INFO', 'ADVERTENCIA', 'CRITICO')
    )
);

CREATE INDEX ix_bitacora_empresa_id ON bitacora (empresa_id);
CREATE INDEX ix_bitacora_usuario_id ON bitacora (usuario_id);
CREATE INDEX ix_bitacora_modulo ON bitacora (modulo);
CREATE INDEX ix_bitacora_accion ON bitacora (accion);
CREATE INDEX ix_bitacora_fecha ON bitacora (fecha);

-- ============================================================
-- Sprint 1 - Reclutamiento
-- ============================================================

CREATE TABLE departamento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    departamento_padre_id UUID REFERENCES departamento(id) ON DELETE RESTRICT,
    responsable_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_departamento_empresa_nombre UNIQUE (empresa_id, nombre)
);

CREATE INDEX ix_departamento_empresa_id ON departamento (empresa_id);
CREATE INDEX ix_departamento_padre_id ON departamento (departamento_padre_id);
CREATE INDEX ix_departamento_responsable_id ON departamento (responsable_id);
CREATE UNIQUE INDEX uq_departamento_empresa_nombre_lower
    ON departamento (empresa_id, lower(nombre));

CREATE TABLE cargo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    departamento_id UUID REFERENCES departamento(id) ON DELETE RESTRICT,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    nivel VARCHAR(30),
    salario_min NUMERIC(12, 2),
    salario_max NUMERIC(12, 2),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_cargo_empresa_nombre UNIQUE (empresa_id, nombre),
    CONSTRAINT ck_cargo_nivel CHECK (
        nivel IS NULL OR nivel IN (
            'OPERATIVO', 'TECNICO', 'SUPERVISOR', 'JEFATURA', 'GERENCIA'
        )
    ),
    CONSTRAINT ck_cargo_salario_min CHECK (salario_min IS NULL OR salario_min >= 0),
    CONSTRAINT ck_cargo_salario_max CHECK (salario_max IS NULL OR salario_max >= 0),
    CONSTRAINT ck_cargo_rango_salario CHECK (
        salario_min IS NULL OR salario_max IS NULL OR salario_max >= salario_min
    )
);

CREATE INDEX ix_cargo_empresa_id ON cargo (empresa_id);
CREATE INDEX ix_cargo_departamento_id ON cargo (departamento_id);
CREATE UNIQUE INDEX uq_cargo_empresa_nombre_lower
    ON cargo (empresa_id, lower(nombre));

CREATE TABLE habilidad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(100),
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_habilidad_empresa_nombre UNIQUE (empresa_id, nombre)
);

CREATE INDEX ix_habilidad_empresa_id ON habilidad (empresa_id);
CREATE UNIQUE INDEX uq_habilidad_empresa_nombre_lower
    ON habilidad (empresa_id, lower(nombre));

CREATE TABLE vacante (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cargo_id UUID NOT NULL REFERENCES cargo(id) ON DELETE RESTRICT,
    departamento_id UUID NOT NULL REFERENCES departamento(id) ON DELETE RESTRICT,
    responsable_id UUID NOT NULL REFERENCES usuario(id) ON DELETE RESTRICT,
    titulo VARCHAR(180) NOT NULL,
    descripcion TEXT NOT NULL,
    requisitos TEXT,
    beneficios TEXT,
    cantidad_vacantes INTEGER NOT NULL DEFAULT 1,
    salario_min NUMERIC(12, 2),
    salario_max NUMERIC(12, 2),
    mostrar_salario BOOLEAN NOT NULL DEFAULT FALSE,
    modalidad VARCHAR(20) NOT NULL,
    ubicacion VARCHAR(160),
    experiencia_min INTEGER NOT NULL DEFAULT 0,
    fecha_publicacion TIMESTAMPTZ,
    fecha_cierre TIMESTAMPTZ,
    estado VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_vacante_cantidad_positiva CHECK (cantidad_vacantes > 0),
    CONSTRAINT ck_vacante_experiencia_no_negativa CHECK (experiencia_min >= 0),
    CONSTRAINT ck_vacante_salario_min CHECK (salario_min IS NULL OR salario_min >= 0),
    CONSTRAINT ck_vacante_salario_max CHECK (salario_max IS NULL OR salario_max >= 0),
    CONSTRAINT ck_vacante_rango_salario CHECK (
        salario_min IS NULL OR salario_max IS NULL OR salario_max >= salario_min
    ),
    CONSTRAINT ck_vacante_fechas CHECK (
        fecha_publicacion IS NULL OR fecha_cierre IS NULL
        OR fecha_cierre >= fecha_publicacion
    ),
    CONSTRAINT ck_vacante_modalidad CHECK (
        modalidad IN ('PRESENCIAL', 'REMOTO', 'HIBRIDO')
    ),
    CONSTRAINT ck_vacante_estado CHECK (
        estado IN ('BORRADOR', 'PUBLICADA', 'PAUSADA', 'CERRADA', 'CANCELADA')
    )
);

CREATE INDEX ix_vacante_empresa_id ON vacante (empresa_id);
CREATE INDEX ix_vacante_cargo_id ON vacante (cargo_id);
CREATE INDEX ix_vacante_departamento_id ON vacante (departamento_id);
CREATE INDEX ix_vacante_responsable_id ON vacante (responsable_id);
CREATE INDEX ix_vacante_estado ON vacante (estado);
CREATE INDEX ix_vacante_fecha_cierre ON vacante (fecha_cierre);

CREATE TABLE vacante_habilidad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacante_id UUID NOT NULL REFERENCES vacante(id) ON DELETE CASCADE,
    habilidad_id UUID NOT NULL REFERENCES habilidad(id) ON DELETE RESTRICT,
    nivel_requerido VARCHAR(30),
    es_obligatorio BOOLEAN NOT NULL DEFAULT TRUE,
    peso NUMERIC(5, 2) NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_vacante_habilidad UNIQUE (vacante_id, habilidad_id),
    CONSTRAINT ck_vacante_habilidad_peso CHECK (peso > 0)
);

CREATE INDEX ix_vacante_habilidad_habilidad_id
    ON vacante_habilidad (habilidad_id);

CREATE TABLE etapa_reclutamiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    orden INTEGER NOT NULL,
    color VARCHAR(30),
    es_inicial BOOLEAN NOT NULL DEFAULT FALSE,
    es_contratado BOOLEAN NOT NULL DEFAULT FALSE,
    es_rechazado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_etapa_empresa_nombre UNIQUE (empresa_id, nombre),
    CONSTRAINT uq_etapa_empresa_orden UNIQUE (empresa_id, orden),
    CONSTRAINT ck_etapa_orden_positivo CHECK (orden > 0)
);

CREATE INDEX ix_etapa_reclutamiento_empresa_id
    ON etapa_reclutamiento (empresa_id);

CREATE TABLE motivo_rechazo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_motivo_rechazo_empresa_nombre UNIQUE (empresa_id, nombre)
);

CREATE INDEX ix_motivo_rechazo_empresa_id ON motivo_rechazo (empresa_id);

CREATE TABLE postulante (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120) NOT NULL,
    ci VARCHAR(30) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telefono VARCHAR(40),
    direccion TEXT,
    ciudad VARCHAR(100),
    fecha_nacimiento DATE,
    cv_url TEXT,
    cv_texto TEXT,
    linkedin TEXT,
    nivel_educativo VARCHAR(20) NOT NULL,
    anios_experiencia INTEGER NOT NULL DEFAULT 0,
    fuente VARCHAR(20) NOT NULL DEFAULT 'PORTAL_WEB',
    en_banco_talento BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_postulante_empresa_ci UNIQUE (empresa_id, ci),
    CONSTRAINT ck_postulante_nivel_educativo CHECK (
        nivel_educativo IN (
            'SECUNDARIA', 'TECNICO', 'LICENCIATURA', 'MAESTRIA', 'DOCTORADO'
        )
    ),
    CONSTRAINT ck_postulante_anios_experiencia CHECK (anios_experiencia >= 0),
    CONSTRAINT ck_postulante_fuente CHECK (
        fuente IN ('PORTAL_WEB', 'APP_MOVIL', 'LINKEDIN', 'REFERIDO', 'FERIA', 'OTRO')
    )
);

CREATE INDEX ix_postulante_empresa_id ON postulante (empresa_id);
CREATE INDEX ix_postulante_email ON postulante (email);
CREATE UNIQUE INDEX uq_postulante_empresa_ci_lower
    ON postulante (empresa_id, lower(ci));

CREATE TABLE postulacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacante_id UUID NOT NULL REFERENCES vacante(id) ON DELETE RESTRICT,
    postulante_id UUID NOT NULL REFERENCES postulante(id) ON DELETE RESTRICT,
    etapa_id UUID NOT NULL REFERENCES etapa_reclutamiento(id) ON DELETE RESTRICT,
    motivo_rechazo_id UUID REFERENCES motivo_rechazo(id) ON DELETE SET NULL,
    empleado_id UUID,
    puntaje_ia NUMERIC(5, 2),
    puntaje_manual NUMERIC(5, 2),
    notas TEXT,
    codigo_seguimiento VARCHAR(40) NOT NULL UNIQUE,
    fecha_postulacion TIMESTAMPTZ NOT NULL DEFAULT now(),
    fecha_ultimo_cambio TIMESTAMPTZ NOT NULL DEFAULT now(),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_postulacion_vacante_postulante
        UNIQUE (vacante_id, postulante_id),
    CONSTRAINT ck_postulacion_puntaje_ia CHECK (
        puntaje_ia IS NULL OR puntaje_ia BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_postulacion_puntaje_manual CHECK (
        puntaje_manual IS NULL OR puntaje_manual BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_postulacion_estado CHECK (
        estado IN ('ACTIVA', 'RETIRADA', 'DESCARTADA', 'CONTRATADA')
    )
);

CREATE INDEX ix_postulacion_vacante_id ON postulacion (vacante_id);
CREATE INDEX ix_postulacion_postulante_id ON postulacion (postulante_id);
CREATE INDEX ix_postulacion_etapa_id ON postulacion (etapa_id);
CREATE INDEX ix_postulacion_motivo_rechazo_id ON postulacion (motivo_rechazo_id);
CREATE INDEX ix_postulacion_estado ON postulacion (estado);

