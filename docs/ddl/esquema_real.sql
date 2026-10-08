-- ============================================================================
-- Sistema SSAS-RRHH · Esquema real de la base de datos (Sprint 2)
-- Generado con: pg_dump --schema-only --no-owner --no-privileges
-- Origen: PostgreSQL 18 · base local migrada a 20261005_0009 (head de Alembic)
-- NOTA: script generado desde la base real; reemplaza el DDL del perfil (DOC-01).
-- ============================================================================


CREATE FUNCTION public.proteger_bitacora() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN RAISE EXCEPTION 'La bitacora es inmutable'; END; $$;

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);

CREATE TABLE public.analisis_cv (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    postulacion_id uuid NOT NULL,
    puntaje_afinidad numeric(5,2) NOT NULL,
    habilidades_detectadas jsonb DEFAULT '[]'::jsonb NOT NULL,
    habilidades_faltantes jsonb DEFAULT '[]'::jsonb NOT NULL,
    anios_experiencia_detectados numeric(5,2),
    resumen_ia text NOT NULL,
    fortalezas jsonb DEFAULT '[]'::jsonb NOT NULL,
    observaciones text,
    modelo_usado character varying(120) NOT NULL,
    tiempo_proceso_ms integer NOT NULL,
    fecha_analisis timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_analisis_cv_afinidad CHECK (((puntaje_afinidad >= (0)::numeric) AND (puntaje_afinidad <= (100)::numeric))),
    CONSTRAINT ck_analisis_cv_experiencia CHECK (((anios_experiencia_detectados IS NULL) OR (anios_experiencia_detectados >= (0)::numeric))),
    CONSTRAINT ck_analisis_cv_fortalezas CHECK ((jsonb_typeof(fortalezas) = 'array'::text)),
    CONSTRAINT ck_analisis_cv_habilidades_detectadas CHECK ((jsonb_typeof(habilidades_detectadas) = 'array'::text)),
    CONSTRAINT ck_analisis_cv_habilidades_faltantes CHECK ((jsonb_typeof(habilidades_faltantes) = 'array'::text)),
    CONSTRAINT ck_analisis_cv_tiempo CHECK ((tiempo_proceso_ms >= 0))
);

CREATE TABLE public.bitacora (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid,
    usuario_id uuid,
    actor_etiqueta character varying(150),
    modulo character varying(80) NOT NULL,
    accion character varying(100) NOT NULL,
    nivel character varying(16) DEFAULT 'INFO'::character varying NOT NULL,
    descripcion text NOT NULL,
    tabla_afectada character varying(100),
    registro_id uuid,
    datos_previos jsonb,
    datos_nuevos jsonb,
    ip_origen inet,
    user_agent text,
    fecha timestamp with time zone DEFAULT now() NOT NULL,
    datos_cifrados bytea NOT NULL,
    nonce_cifrado bytea NOT NULL,
    version_cifrado integer DEFAULT 1 NOT NULL,
    hash_anterior character varying(64),
    hash_registro character varying(64) NOT NULL
);

CREATE TABLE public.cargo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    departamento_id uuid,
    nombre character varying(120) NOT NULL,
    codigo character varying(40),
    descripcion text,
    nivel character varying(80),
    salario_min numeric(12,2),
    salario_max numeric(12,2),
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_cargo_rango_salario CHECK (((salario_min IS NULL) OR (salario_max IS NULL) OR (salario_max >= salario_min))),
    CONSTRAINT ck_cargo_salario_max_no_negativo CHECK (((salario_max IS NULL) OR (salario_max >= (0)::numeric))),
    CONSTRAINT ck_cargo_salario_min_no_negativo CHECK (((salario_min IS NULL) OR (salario_min >= (0)::numeric)))
);

CREATE TABLE public.conocimiento_articulo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    titulo character varying(160) NOT NULL,
    contenido text NOT NULL,
    categoria character varying(80) DEFAULT 'General'::character varying NOT NULL,
    publico boolean DEFAULT false NOT NULL,
    publicado boolean DEFAULT false NOT NULL,
    actualizado_en timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.conocimiento_fragmento (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    articulo_id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    orden integer NOT NULL,
    texto text NOT NULL,
    vector jsonb NOT NULL,
    modelo character varying(80) NOT NULL
);

CREATE TABLE public.departamento (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    nombre character varying(120) NOT NULL,
    codigo character varying(40),
    descripcion text,
    departamento_padre_id uuid,
    responsable_id uuid,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.email_verification_token (
    id uuid NOT NULL,
    empresa_id uuid,
    usuario_id uuid NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.empleado (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    usuario_id uuid,
    codigo character varying(40) NOT NULL,
    nombres character varying(120) NOT NULL,
    apellido_paterno character varying(120) NOT NULL,
    apellido_materno character varying(120),
    ci character varying(30) NOT NULL,
    ci_expedido character varying(10) NOT NULL,
    fecha_nacimiento date,
    genero character varying(20),
    estado_civil character varying(30),
    direccion text,
    telefono character varying(40),
    email_personal character varying(150),
    contacto_emergencia character varying(200),
    telefono_emergencia character varying(40),
    nua_cua character varying(40),
    afp character varying(80),
    banco character varying(120),
    numero_cuenta character varying(80),
    tipo_cuenta character varying(40),
    fecha_ingreso date NOT NULL,
    fecha_salida date,
    motivo_salida text,
    estado character varying(20) DEFAULT 'ACTIVO'::character varying NOT NULL,
    foto_url text,
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_empleado_estado CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))),
    CONSTRAINT ck_empleado_fechas CHECK (((fecha_salida IS NULL) OR (fecha_salida >= fecha_ingreso)))
);

CREATE TABLE public.empresa (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nit character varying(30),
    razon_social character varying(200) NOT NULL,
    nombre_comercial character varying(200) NOT NULL,
    slug character varying(120) NOT NULL,
    email character varying(150),
    telefono character varying(40),
    direccion text,
    ciudad character varying(100),
    logo_url text,
    descripcion text,
    color_primario character varying(20) DEFAULT '#2563eb'::character varying NOT NULL,
    portal_publico_activo boolean DEFAULT true NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    eliminado_at timestamp with time zone,
    eliminado_por_id uuid,
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_empresa_slug_no_vacio CHECK ((length(TRIM(BOTH FROM slug)) > 0))
);

CREATE TABLE public.empresa_modulo (
    empresa_id uuid NOT NULL,
    modulo_id uuid NOT NULL,
    habilitado boolean DEFAULT true NOT NULL,
    fecha_habilitacion timestamp with time zone,
    habilitado_por_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.entrevista (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    postulacion_id uuid NOT NULL,
    entrevistador_id uuid NOT NULL,
    tipo character varying(40) NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    duracion_min integer NOT NULL,
    modalidad character varying(20) NOT NULL,
    enlace_reunion text,
    lugar text,
    estado character varying(20) DEFAULT 'PROGRAMADA'::character varying NOT NULL,
    puntaje numeric(5,2),
    observaciones text,
    recomendacion character varying(40),
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_entrevista_duracion CHECK ((duracion_min > 0)),
    CONSTRAINT ck_entrevista_estado CHECK (((estado)::text = ANY ((ARRAY['PROGRAMADA'::character varying, 'CONFIRMADA'::character varying, 'REALIZADA'::character varying, 'CANCELADA'::character varying])::text[]))),
    CONSTRAINT ck_entrevista_modalidad CHECK (((modalidad)::text = ANY ((ARRAY['VIRTUAL'::character varying, 'PRESENCIAL'::character varying, 'TELEFONICA'::character varying])::text[]))),
    CONSTRAINT ck_entrevista_puntaje CHECK (((puntaje IS NULL) OR ((puntaje >= (0)::numeric) AND (puntaje <= (100)::numeric)))),
    CONSTRAINT ck_entrevista_ubicacion CHECK (((((modalidad)::text = 'VIRTUAL'::text) AND (enlace_reunion IS NOT NULL) AND (length(TRIM(BOTH FROM enlace_reunion)) > 0)) OR (((modalidad)::text = 'PRESENCIAL'::text) AND (lugar IS NOT NULL) AND (length(TRIM(BOTH FROM lugar)) > 0)) OR ((modalidad)::text = 'TELEFONICA'::text)))
);

CREATE TABLE public.etapa_reclutamiento (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    orden integer NOT NULL,
    color character varying(30),
    es_inicial boolean DEFAULT false NOT NULL,
    es_contratado boolean DEFAULT false NOT NULL,
    es_rechazado boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_etapa_reclutamiento_orden_positivo CHECK ((orden > 0))
);

CREATE TABLE public.evaluacion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    postulacion_id uuid NOT NULL,
    evaluador_id uuid NOT NULL,
    tipo character varying(40) NOT NULL,
    nombre character varying(150) NOT NULL,
    puntaje numeric(10,2) NOT NULL,
    puntaje_maximo numeric(10,2) NOT NULL,
    aprobado boolean NOT NULL,
    archivo_url text,
    observaciones text,
    fecha timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_evaluacion_puntaje CHECK (((puntaje_maximo > (0)::numeric) AND (puntaje >= (0)::numeric) AND (puntaje <= puntaje_maximo)))
);

CREATE TABLE public.habilidad (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    nombre character varying(120) NOT NULL,
    categoria character varying(120),
    descripcion text,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.modulo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo character varying(60) NOT NULL,
    nombre character varying(120) NOT NULL,
    descripcion text,
    icono character varying(60),
    orden integer DEFAULT 100 NOT NULL,
    es_core boolean DEFAULT false NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.motivo_rechazo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    nombre character varying(120) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.parametro_legal (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo character varying(80) NOT NULL,
    nombre character varying(160) NOT NULL,
    descripcion text,
    tipo_valor character varying(30) NOT NULL,
    pais character varying(80) NOT NULL
);

CREATE TABLE public.parametro_valor (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    parametro_id uuid NOT NULL,
    valor jsonb NOT NULL,
    vigente_desde date NOT NULL,
    vigente_hasta date NOT NULL,
    norma_legal text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.password_reset_token (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid,
    usuario_id uuid NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.permiso (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo character varying(120) NOT NULL,
    modulo character varying(80) NOT NULL,
    recurso character varying(80) NOT NULL,
    operacion character varying(80) NOT NULL,
    descripcion text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.plan_modulo (
    plan_id uuid NOT NULL,
    modulo_id uuid NOT NULL
);

CREATE TABLE public.plan_suscripcion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nombre character varying(120) NOT NULL,
    precio_mensual numeric(12,2) NOT NULL,
    max_empleados integer NOT NULL,
    modulos jsonb DEFAULT '{}'::jsonb NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    descripcion text,
    moneda character varying(3) DEFAULT 'USD'::character varying NOT NULL,
    max_usuarios integer DEFAULT 5 NOT NULL,
    max_vacantes_activas integer DEFAULT 5 NOT NULL,
    max_almacenamiento_mb integer DEFAULT 250 NOT NULL,
    stripe_price_id character varying(120),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.postulacion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    vacante_id uuid NOT NULL,
    postulante_id uuid NOT NULL,
    etapa_id uuid NOT NULL,
    motivo_rechazo_id uuid,
    empleado_id uuid,
    puntaje_ia numeric(5,2),
    puntaje_manual numeric(5,2),
    notas text,
    codigo_seguimiento character varying(40) NOT NULL,
    fecha_postulacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_ultimo_cambio timestamp with time zone DEFAULT now() NOT NULL,
    estado character varying(20) DEFAULT 'ACTIVA'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_postulacion_estado CHECK (((estado)::text = ANY ((ARRAY['ACTIVA'::character varying, 'RETIRADA'::character varying, 'DESCARTADA'::character varying, 'CONTRATADA'::character varying])::text[]))),
    CONSTRAINT ck_postulacion_puntaje_ia CHECK (((puntaje_ia IS NULL) OR ((puntaje_ia >= (0)::numeric) AND (puntaje_ia <= (100)::numeric)))),
    CONSTRAINT ck_postulacion_puntaje_manual CHECK (((puntaje_manual IS NULL) OR ((puntaje_manual >= (0)::numeric) AND (puntaje_manual <= (100)::numeric))))
);

CREATE TABLE public.postulacion_nota (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    postulacion_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    contenido text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.postulante (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    nombres character varying(120) NOT NULL,
    apellidos character varying(120) NOT NULL,
    ci character varying(30) NOT NULL,
    email character varying(150) NOT NULL,
    telefono character varying(40) NOT NULL,
    direccion text,
    ciudad character varying(100) NOT NULL,
    fecha_nacimiento date,
    cv_url text,
    cv_texto text,
    linkedin text,
    nivel_educativo character varying(20) NOT NULL,
    anios_experiencia integer DEFAULT 0 NOT NULL,
    fuente character varying(20) NOT NULL,
    en_banco_talento boolean DEFAULT false NOT NULL,
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_postulante_experiencia_no_negativa CHECK ((anios_experiencia >= 0)),
    CONSTRAINT ck_postulante_fuente CHECK (((fuente)::text = ANY ((ARRAY['PORTAL_WEB'::character varying, 'APP_MOVIL'::character varying, 'LINKEDIN'::character varying, 'REFERIDO'::character varying, 'FERIA'::character varying, 'OTRO'::character varying])::text[]))),
    CONSTRAINT ck_postulante_nivel_educativo CHECK (((nivel_educativo)::text = ANY ((ARRAY['SECUNDARIA'::character varying, 'TECNICO'::character varying, 'LICENCIATURA'::character varying, 'MAESTRIA'::character varying, 'DOCTORADO'::character varying])::text[])))
);

CREATE TABLE public.postulante_habilidad (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    postulante_id uuid NOT NULL,
    habilidad_id uuid NOT NULL,
    nivel character varying(30),
    anios_experiencia numeric(5,2) DEFAULT 0 NOT NULL,
    detectado_por_ia boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_postulante_habilidad_experiencia CHECK ((anios_experiencia >= (0)::numeric))
);

CREATE TABLE public.refresh_token (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid,
    usuario_id uuid NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.reporte_definicion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    nombre character varying(160) NOT NULL,
    fuente character varying(60) NOT NULL,
    columnas jsonb NOT NULL,
    filtros jsonb DEFAULT '[]'::jsonb NOT NULL,
    orden jsonb DEFAULT '[]'::jsonb NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    fecha_actualizacion timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.reporte_ejecucion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    reporte_id uuid,
    usuario_id uuid NOT NULL,
    formato character varying(20) NOT NULL,
    filtros_aplicados jsonb DEFAULT '[]'::jsonb NOT NULL,
    estado character varying(20) NOT NULL,
    cantidad_registros integer,
    fecha_inicio timestamp with time zone DEFAULT now() NOT NULL,
    fecha_fin timestamp with time zone,
    error text
);

CREATE TABLE public.respaldo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nombre character varying(255) NOT NULL,
    ruta_storage text,
    formato character varying(20) NOT NULL,
    tamano_bytes bigint,
    sha256 character varying(64),
    estado character varying(30) NOT NULL,
    creado_por_id uuid NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_finalizacion timestamp with time zone,
    fecha_restauracion timestamp with time zone,
    restaurado_por_id uuid,
    mensaje_error text
);

CREATE TABLE public.rol (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid,
    nombre character varying(120) NOT NULL,
    codigo character varying(80) NOT NULL,
    descripcion text,
    es_sistema boolean DEFAULT false NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.rol_permiso (
    rol_id uuid NOT NULL,
    permiso_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.stripe_evento (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    stripe_event_id character varying(120) NOT NULL,
    tipo character varying(120) NOT NULL,
    estado_procesamiento character varying(30) NOT NULL,
    fecha_recepcion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_procesamiento timestamp with time zone,
    intentos integer DEFAULT 1 NOT NULL,
    error text
);

CREATE TABLE public.suscripcion (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    fecha_inicio date DEFAULT CURRENT_DATE NOT NULL,
    fecha_fin date,
    estado character varying(30) DEFAULT 'ACTIVA'::character varying NOT NULL,
    periodo_prueba_hasta date,
    stripe_customer_id character varying(120),
    stripe_subscription_id character varying(120),
    stripe_checkout_session_id character varying(120),
    fecha_ultimo_pago timestamp with time zone,
    fecha_proximo_cobro timestamp with time zone,
    creado_por_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    cancelar_al_fin_periodo boolean DEFAULT false NOT NULL
);

CREATE TABLE public.usuario (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid,
    nombres character varying(120) NOT NULL,
    apellidos character varying(120) DEFAULT ''::character varying NOT NULL,
    email character varying(150) NOT NULL,
    username character varying(80) NOT NULL,
    password_hash text NOT NULL,
    telefono character varying(40),
    ultimo_acceso timestamp with time zone,
    debe_cambiar_password boolean DEFAULT false NOT NULL,
    intentos_fallidos integer DEFAULT 0 NOT NULL,
    bloqueado_hasta timestamp with time zone,
    ultimo_intento_fallido timestamp with time zone,
    activo boolean DEFAULT true NOT NULL,
    email_verified boolean DEFAULT false NOT NULL,
    eliminado_at timestamp with time zone,
    eliminado_por_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_usuario_intentos_fallidos_no_negativo CHECK ((intentos_fallidos >= 0))
);

CREATE TABLE public.usuario_rol (
    usuario_id uuid NOT NULL,
    rol_id uuid NOT NULL,
    asignado_por_id uuid,
    fecha_asignacion timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.vacante (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    empresa_id uuid NOT NULL,
    cargo_id uuid NOT NULL,
    departamento_id uuid NOT NULL,
    responsable_id uuid NOT NULL,
    titulo character varying(180) NOT NULL,
    descripcion text NOT NULL,
    requisitos text,
    beneficios text,
    cantidad_vacantes integer DEFAULT 1 NOT NULL,
    salario_min numeric(12,2),
    salario_max numeric(12,2),
    mostrar_salario boolean DEFAULT false NOT NULL,
    modalidad character varying(20) NOT NULL,
    ubicacion character varying(160),
    experiencia_min integer DEFAULT 0 NOT NULL,
    fecha_publicacion timestamp with time zone,
    fecha_cierre timestamp with time zone,
    estado character varying(20) DEFAULT 'BORRADOR'::character varying NOT NULL,
    fecha_registro timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_vacante_cantidad_positiva CHECK ((cantidad_vacantes > 0)),
    CONSTRAINT ck_vacante_estado CHECK (((estado)::text = ANY ((ARRAY['BORRADOR'::character varying, 'PUBLICADA'::character varying, 'PAUSADA'::character varying, 'CERRADA'::character varying, 'CANCELADA'::character varying])::text[]))),
    CONSTRAINT ck_vacante_experiencia_no_negativa CHECK ((experiencia_min >= 0)),
    CONSTRAINT ck_vacante_fechas CHECK (((fecha_cierre IS NULL) OR (fecha_publicacion IS NULL) OR (fecha_cierre >= fecha_publicacion))),
    CONSTRAINT ck_vacante_modalidad CHECK (((modalidad)::text = ANY ((ARRAY['PRESENCIAL'::character varying, 'REMOTO'::character varying, 'HIBRIDO'::character varying])::text[]))),
    CONSTRAINT ck_vacante_rango_salario CHECK (((salario_min IS NULL) OR (salario_max IS NULL) OR (salario_max >= salario_min))),
    CONSTRAINT ck_vacante_salario_max_no_negativo CHECK (((salario_max IS NULL) OR (salario_max >= (0)::numeric))),
    CONSTRAINT ck_vacante_salario_min_no_negativo CHECK (((salario_min IS NULL) OR (salario_min >= (0)::numeric)))
);

CREATE TABLE public.vacante_habilidad (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    vacante_id uuid NOT NULL,
    habilidad_id uuid NOT NULL,
    nivel_requerido character varying(30) NOT NULL,
    es_obligatorio boolean DEFAULT true NOT NULL,
    peso numeric(5,2) DEFAULT 1.00 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_vacante_habilidad_peso_positivo CHECK ((peso > (0)::numeric))
);

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

ALTER TABLE ONLY public.analisis_cv
    ADD CONSTRAINT analisis_cv_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT cargo_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.conocimiento_articulo
    ADD CONSTRAINT conocimiento_articulo_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.conocimiento_fragmento
    ADD CONSTRAINT conocimiento_fragmento_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.departamento
    ADD CONSTRAINT departamento_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.email_verification_token
    ADD CONSTRAINT email_verification_token_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.email_verification_token
    ADD CONSTRAINT email_verification_token_token_hash_key UNIQUE (token_hash);

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.empresa_modulo
    ADD CONSTRAINT empresa_modulo_pkey PRIMARY KEY (empresa_id, modulo_id);

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_nit_key UNIQUE (nit);

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_slug_key UNIQUE (slug);

ALTER TABLE ONLY public.entrevista
    ADD CONSTRAINT entrevista_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.etapa_reclutamiento
    ADD CONSTRAINT etapa_reclutamiento_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.habilidad
    ADD CONSTRAINT habilidad_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.modulo
    ADD CONSTRAINT modulo_codigo_key UNIQUE (codigo);

ALTER TABLE ONLY public.modulo
    ADD CONSTRAINT modulo_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.motivo_rechazo
    ADD CONSTRAINT motivo_rechazo_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.parametro_legal
    ADD CONSTRAINT parametro_legal_codigo_key UNIQUE (codigo);

ALTER TABLE ONLY public.parametro_legal
    ADD CONSTRAINT parametro_legal_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.parametro_valor
    ADD CONSTRAINT parametro_valor_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.password_reset_token
    ADD CONSTRAINT password_reset_token_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.plan_suscripcion
    ADD CONSTRAINT plan_suscripcion_nombre_key UNIQUE (nombre);

ALTER TABLE ONLY public.plan_suscripcion
    ADD CONSTRAINT plan_suscripcion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.postulacion_nota
    ADD CONSTRAINT postulacion_nota_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT postulacion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.postulante_habilidad
    ADD CONSTRAINT postulante_habilidad_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.postulante
    ADD CONSTRAINT postulante_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.refresh_token
    ADD CONSTRAINT refresh_token_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reporte_definicion
    ADD CONSTRAINT reporte_definicion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reporte_ejecucion
    ADD CONSTRAINT reporte_ejecucion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.respaldo
    ADD CONSTRAINT respaldo_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (rol_id, permiso_id);

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.stripe_evento
    ADD CONSTRAINT stripe_evento_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.stripe_evento
    ADD CONSTRAINT stripe_evento_stripe_event_id_key UNIQUE (stripe_event_id);

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT uq_bitacora_hash_registro UNIQUE (hash_registro);

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT uq_cargo_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.departamento
    ADD CONSTRAINT uq_departamento_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT uq_empleado_empresa_ci UNIQUE (empresa_id, ci);

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT uq_empleado_empresa_codigo UNIQUE (empresa_id, codigo);

ALTER TABLE ONLY public.etapa_reclutamiento
    ADD CONSTRAINT uq_etapa_reclutamiento_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.etapa_reclutamiento
    ADD CONSTRAINT uq_etapa_reclutamiento_empresa_orden UNIQUE (empresa_id, orden);

ALTER TABLE ONLY public.habilidad
    ADD CONSTRAINT uq_habilidad_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.motivo_rechazo
    ADD CONSTRAINT uq_motivo_rechazo_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT uq_permiso_modulo_recurso_operacion UNIQUE (modulo, recurso, operacion);

ALTER TABLE ONLY public.plan_modulo
    ADD CONSTRAINT uq_plan_modulo PRIMARY KEY (plan_id, modulo_id);

ALTER TABLE ONLY public.plan_suscripcion
    ADD CONSTRAINT uq_plan_stripe_price UNIQUE (stripe_price_id);

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT uq_postulacion_codigo_seguimiento UNIQUE (codigo_seguimiento);

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT uq_postulacion_vacante_postulante UNIQUE (vacante_id, postulante_id);

ALTER TABLE ONLY public.postulante
    ADD CONSTRAINT uq_postulante_empresa_ci UNIQUE (empresa_id, ci);

ALTER TABLE ONLY public.postulante_habilidad
    ADD CONSTRAINT uq_postulante_habilidad_postulante_habilidad UNIQUE (postulante_id, habilidad_id);

ALTER TABLE ONLY public.reporte_definicion
    ADD CONSTRAINT uq_reporte_definicion_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT uq_rol_empresa_codigo UNIQUE (empresa_id, codigo);

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT uq_rol_empresa_nombre UNIQUE (empresa_id, nombre);

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT uq_suscripcion_empresa UNIQUE (empresa_id);

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT uq_suscripcion_stripe_checkout UNIQUE (stripe_checkout_session_id);

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT uq_suscripcion_stripe_customer UNIQUE (stripe_customer_id);

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT uq_suscripcion_stripe_subscription UNIQUE (stripe_subscription_id);

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT uq_usuario_empresa_email UNIQUE (empresa_id, email);

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT uq_usuario_empresa_username UNIQUE (empresa_id, username);

ALTER TABLE ONLY public.vacante_habilidad
    ADD CONSTRAINT uq_vacante_habilidad_pair UNIQUE (vacante_id, habilidad_id);

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.usuario_rol
    ADD CONSTRAINT usuario_rol_pkey PRIMARY KEY (usuario_id, rol_id);

ALTER TABLE ONLY public.vacante_habilidad
    ADD CONSTRAINT vacante_habilidad_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.vacante
    ADD CONSTRAINT vacante_pkey PRIMARY KEY (id);

CREATE INDEX idx_analisis_cv_fecha_analisis ON public.analisis_cv USING btree (fecha_analisis);

CREATE INDEX idx_analisis_cv_postulacion_id_fecha_analisis ON public.analisis_cv USING btree (postulacion_id, fecha_analisis);

CREATE INDEX idx_bitacora_accion ON public.bitacora USING btree (accion);

CREATE INDEX idx_bitacora_empresa_id ON public.bitacora USING btree (empresa_id);

CREATE INDEX idx_bitacora_fecha ON public.bitacora USING btree (fecha);

CREATE INDEX idx_bitacora_modulo ON public.bitacora USING btree (modulo);

CREATE INDEX idx_bitacora_usuario_id ON public.bitacora USING btree (usuario_id);

CREATE INDEX idx_cargo_departamento_id ON public.cargo USING btree (departamento_id);

CREATE INDEX idx_cargo_empresa_id ON public.cargo USING btree (empresa_id);

CREATE INDEX idx_departamento_empresa_id ON public.departamento USING btree (empresa_id);

CREATE INDEX idx_departamento_padre_id ON public.departamento USING btree (departamento_padre_id);

CREATE INDEX idx_departamento_responsable_id ON public.departamento USING btree (responsable_id);

CREATE INDEX idx_email_verification_token_expires_at ON public.email_verification_token USING btree (expires_at);

CREATE INDEX idx_email_verification_token_usuario_id ON public.email_verification_token USING btree (usuario_id);

CREATE INDEX idx_empleado_empresa_id ON public.empleado USING btree (empresa_id);

CREATE INDEX idx_empleado_empresa_id_estado ON public.empleado USING btree (empresa_id, estado);

CREATE INDEX idx_empleado_fecha_ingreso ON public.empleado USING btree (fecha_ingreso);

CREATE INDEX idx_empleado_usuario_id ON public.empleado USING btree (usuario_id);

CREATE INDEX idx_empresa_eliminado_at ON public.empresa USING btree (eliminado_at);

CREATE INDEX idx_empresa_modulo_empresa_id ON public.empresa_modulo USING btree (empresa_id);

CREATE INDEX idx_entrevista_entrevistador_id_fecha_hora ON public.entrevista USING btree (entrevistador_id, fecha_hora);

CREATE INDEX idx_entrevista_estado ON public.entrevista USING btree (estado);

CREATE INDEX idx_entrevista_fecha_hora ON public.entrevista USING btree (fecha_hora);

CREATE INDEX idx_entrevista_postulacion_id ON public.entrevista USING btree (postulacion_id);

CREATE INDEX idx_etapa_reclutamiento_empresa_id ON public.etapa_reclutamiento USING btree (empresa_id);

CREATE INDEX idx_evaluacion_evaluador_id ON public.evaluacion USING btree (evaluador_id);

CREATE INDEX idx_evaluacion_fecha ON public.evaluacion USING btree (fecha);

CREATE INDEX idx_evaluacion_postulacion_id_fecha ON public.evaluacion USING btree (postulacion_id, fecha);

CREATE INDEX idx_habilidad_empresa_id ON public.habilidad USING btree (empresa_id);

CREATE INDEX idx_motivo_rechazo_empresa_id ON public.motivo_rechazo USING btree (empresa_id);

CREATE INDEX idx_parametro_valor_parametro_vigencia ON public.parametro_valor USING btree (parametro_id, vigente_desde);

CREATE INDEX idx_password_reset_token_empresa_id ON public.password_reset_token USING btree (empresa_id);

CREATE INDEX idx_password_reset_token_expires_at ON public.password_reset_token USING btree (expires_at);

CREATE INDEX idx_password_reset_token_usuario_id ON public.password_reset_token USING btree (usuario_id);

CREATE INDEX idx_postulacion_codigo_seguimiento ON public.postulacion USING btree (codigo_seguimiento);

CREATE INDEX idx_postulacion_empleado_id ON public.postulacion USING btree (empleado_id);

CREATE INDEX idx_postulacion_estado ON public.postulacion USING btree (estado);

CREATE INDEX idx_postulacion_etapa_id ON public.postulacion USING btree (etapa_id);

CREATE INDEX idx_postulacion_motivo_rechazo_id ON public.postulacion USING btree (motivo_rechazo_id);

CREATE INDEX idx_postulacion_nota_postulacion_id ON public.postulacion_nota USING btree (postulacion_id);

CREATE INDEX idx_postulacion_nota_usuario_id ON public.postulacion_nota USING btree (usuario_id);

CREATE INDEX idx_postulacion_postulante_id ON public.postulacion USING btree (postulante_id);

CREATE INDEX idx_postulacion_vacante_id ON public.postulacion USING btree (vacante_id);

CREATE INDEX idx_postulante_email ON public.postulante USING btree (email);

CREATE INDEX idx_postulante_empresa_id ON public.postulante USING btree (empresa_id);

CREATE INDEX idx_postulante_habilidad_habilidad_id ON public.postulante_habilidad USING btree (habilidad_id);

CREATE INDEX idx_postulante_habilidad_postulante_id ON public.postulante_habilidad USING btree (postulante_id);

CREATE INDEX idx_refresh_token_empresa_id ON public.refresh_token USING btree (empresa_id);

CREATE INDEX idx_refresh_token_expires_at ON public.refresh_token USING btree (expires_at);

CREATE INDEX idx_refresh_token_usuario_id ON public.refresh_token USING btree (usuario_id);

CREATE INDEX idx_reporte_definicion_empresa ON public.reporte_definicion USING btree (empresa_id);

CREATE INDEX idx_reporte_ejecucion_empresa_fecha ON public.reporte_ejecucion USING btree (empresa_id, fecha_inicio);

CREATE INDEX idx_respaldo_estado ON public.respaldo USING btree (estado);

CREATE INDEX idx_respaldo_fecha_creacion ON public.respaldo USING btree (fecha_creacion);

CREATE INDEX idx_rol_empresa_id ON public.rol USING btree (empresa_id);

CREATE INDEX idx_rol_permiso_permiso_id ON public.rol_permiso USING btree (permiso_id);

CREATE INDEX idx_rol_permiso_rol_id ON public.rol_permiso USING btree (rol_id);

CREATE INDEX idx_usuario_bloqueado_hasta ON public.usuario USING btree (bloqueado_hasta);

CREATE INDEX idx_usuario_eliminado_at ON public.usuario USING btree (eliminado_at);

CREATE INDEX idx_usuario_email ON public.usuario USING btree (email);

CREATE INDEX idx_usuario_empresa_id ON public.usuario USING btree (empresa_id);

CREATE INDEX idx_usuario_rol_rol_id ON public.usuario_rol USING btree (rol_id);

CREATE INDEX idx_usuario_rol_usuario_id ON public.usuario_rol USING btree (usuario_id);

CREATE INDEX idx_vacante_cargo_id ON public.vacante USING btree (cargo_id);

CREATE INDEX idx_vacante_departamento_id ON public.vacante USING btree (departamento_id);

CREATE INDEX idx_vacante_empresa_id ON public.vacante USING btree (empresa_id);

CREATE INDEX idx_vacante_estado ON public.vacante USING btree (estado);

CREATE INDEX idx_vacante_fecha_cierre ON public.vacante USING btree (fecha_cierre);

CREATE INDEX idx_vacante_habilidad_habilidad_id ON public.vacante_habilidad USING btree (habilidad_id);

CREATE INDEX idx_vacante_responsable_id ON public.vacante USING btree (responsable_id);

CREATE INDEX ix_conocimiento_articulo_empresa ON public.conocimiento_articulo USING btree (empresa_id);

CREATE INDEX ix_conocimiento_fragmento_empresa ON public.conocimiento_fragmento USING btree (empresa_id);

CREATE UNIQUE INDEX uq_cargo_empresa_nombre_ci ON public.cargo USING btree (empresa_id, lower((nombre)::text));

CREATE UNIQUE INDEX uq_departamento_empresa_nombre_ci ON public.departamento USING btree (empresa_id, lower((nombre)::text));

CREATE UNIQUE INDEX uq_empleado_empresa_ci_ci ON public.empleado USING btree (empresa_id, lower((ci)::text));

CREATE UNIQUE INDEX uq_empleado_empresa_codigo_ci ON public.empleado USING btree (empresa_id, lower((codigo)::text));

CREATE UNIQUE INDEX uq_empresa_slug_ci ON public.empresa USING btree (lower((slug)::text));

CREATE UNIQUE INDEX uq_habilidad_empresa_nombre_ci ON public.habilidad USING btree (empresa_id, lower((nombre)::text));

CREATE UNIQUE INDEX uq_postulante_empresa_ci_ci ON public.postulante USING btree (empresa_id, lower((ci)::text));

CREATE UNIQUE INDEX uq_rol_empresa_codigo_ci ON public.rol USING btree (empresa_id, lower((codigo)::text));

CREATE UNIQUE INDEX uq_rol_empresa_nombre_ci ON public.rol USING btree (empresa_id, lower((nombre)::text));

CREATE UNIQUE INDEX uq_rol_global_codigo_ci ON public.rol USING btree (lower((codigo)::text)) WHERE (empresa_id IS NULL);

CREATE UNIQUE INDEX uq_rol_global_nombre_ci ON public.rol USING btree (lower((nombre)::text)) WHERE (empresa_id IS NULL);

CREATE UNIQUE INDEX uq_usuario_empresa_email_ci ON public.usuario USING btree (empresa_id, lower((email)::text));

CREATE UNIQUE INDEX uq_usuario_empresa_username_ci ON public.usuario USING btree (empresa_id, lower((username)::text));

CREATE UNIQUE INDEX uq_usuario_plataforma_email_ci ON public.usuario USING btree (lower((email)::text)) WHERE (empresa_id IS NULL);

CREATE UNIQUE INDEX uq_usuario_plataforma_username_ci ON public.usuario USING btree (lower((username)::text)) WHERE (empresa_id IS NULL);

CREATE TRIGGER trg_bitacora_inmutable BEFORE DELETE OR UPDATE ON public.bitacora FOR EACH ROW EXECUTE FUNCTION public.proteger_bitacora();

ALTER TABLE ONLY public.analisis_cv
    ADD CONSTRAINT analisis_cv_postulacion_id_fkey FOREIGN KEY (postulacion_id) REFERENCES public.postulacion(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT cargo_departamento_id_fkey FOREIGN KEY (departamento_id) REFERENCES public.departamento(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT cargo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.conocimiento_articulo
    ADD CONSTRAINT conocimiento_articulo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id);

ALTER TABLE ONLY public.conocimiento_fragmento
    ADD CONSTRAINT conocimiento_fragmento_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.conocimiento_articulo(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.conocimiento_fragmento
    ADD CONSTRAINT conocimiento_fragmento_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id);

ALTER TABLE ONLY public.departamento
    ADD CONSTRAINT departamento_departamento_padre_id_fkey FOREIGN KEY (departamento_padre_id) REFERENCES public.departamento(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.departamento
    ADD CONSTRAINT departamento_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.departamento
    ADD CONSTRAINT departamento_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.usuario(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.email_verification_token
    ADD CONSTRAINT email_verification_token_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.email_verification_token
    ADD CONSTRAINT email_verification_token_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.empresa_modulo
    ADD CONSTRAINT empresa_modulo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.empresa_modulo
    ADD CONSTRAINT empresa_modulo_modulo_id_fkey FOREIGN KEY (modulo_id) REFERENCES public.modulo(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.entrevista
    ADD CONSTRAINT entrevista_entrevistador_id_fkey FOREIGN KEY (entrevistador_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.entrevista
    ADD CONSTRAINT entrevista_postulacion_id_fkey FOREIGN KEY (postulacion_id) REFERENCES public.postulacion(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.etapa_reclutamiento
    ADD CONSTRAINT etapa_reclutamiento_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_evaluador_id_fkey FOREIGN KEY (evaluador_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_postulacion_id_fkey FOREIGN KEY (postulacion_id) REFERENCES public.postulacion(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT fk_postulacion_empleado_id FOREIGN KEY (empleado_id) REFERENCES public.empleado(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.habilidad
    ADD CONSTRAINT habilidad_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.motivo_rechazo
    ADD CONSTRAINT motivo_rechazo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.parametro_valor
    ADD CONSTRAINT parametro_valor_parametro_id_fkey FOREIGN KEY (parametro_id) REFERENCES public.parametro_legal(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.password_reset_token
    ADD CONSTRAINT password_reset_token_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.password_reset_token
    ADD CONSTRAINT password_reset_token_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.plan_modulo
    ADD CONSTRAINT plan_modulo_modulo_id_fkey FOREIGN KEY (modulo_id) REFERENCES public.modulo(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.plan_modulo
    ADD CONSTRAINT plan_modulo_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.plan_suscripcion(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT postulacion_etapa_id_fkey FOREIGN KEY (etapa_id) REFERENCES public.etapa_reclutamiento(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT postulacion_motivo_rechazo_id_fkey FOREIGN KEY (motivo_rechazo_id) REFERENCES public.motivo_rechazo(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.postulacion_nota
    ADD CONSTRAINT postulacion_nota_postulacion_id_fkey FOREIGN KEY (postulacion_id) REFERENCES public.postulacion(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.postulacion_nota
    ADD CONSTRAINT postulacion_nota_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT postulacion_postulante_id_fkey FOREIGN KEY (postulante_id) REFERENCES public.postulante(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulacion
    ADD CONSTRAINT postulacion_vacante_id_fkey FOREIGN KEY (vacante_id) REFERENCES public.vacante(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulante
    ADD CONSTRAINT postulante_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.postulante_habilidad
    ADD CONSTRAINT postulante_habilidad_habilidad_id_fkey FOREIGN KEY (habilidad_id) REFERENCES public.habilidad(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.postulante_habilidad
    ADD CONSTRAINT postulante_habilidad_postulante_id_fkey FOREIGN KEY (postulante_id) REFERENCES public.postulante(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.refresh_token
    ADD CONSTRAINT refresh_token_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.refresh_token
    ADD CONSTRAINT refresh_token_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reporte_definicion
    ADD CONSTRAINT reporte_definicion_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reporte_definicion
    ADD CONSTRAINT reporte_definicion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.reporte_ejecucion
    ADD CONSTRAINT reporte_ejecucion_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reporte_ejecucion
    ADD CONSTRAINT reporte_ejecucion_reporte_id_fkey FOREIGN KEY (reporte_id) REFERENCES public.reporte_definicion(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.reporte_ejecucion
    ADD CONSTRAINT reporte_ejecucion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.respaldo
    ADD CONSTRAINT respaldo_creado_por_id_fkey FOREIGN KEY (creado_por_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.respaldo
    ADD CONSTRAINT respaldo_restaurado_por_id_fkey FOREIGN KEY (restaurado_por_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_permiso_id_fkey FOREIGN KEY (permiso_id) REFERENCES public.permiso(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_creado_por_id_fkey FOREIGN KEY (creado_por_id) REFERENCES public.usuario(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.plan_suscripcion(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.usuario_rol
    ADD CONSTRAINT usuario_rol_asignado_por_id_fkey FOREIGN KEY (asignado_por_id) REFERENCES public.usuario(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.usuario_rol
    ADD CONSTRAINT usuario_rol_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.usuario_rol
    ADD CONSTRAINT usuario_rol_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.vacante
    ADD CONSTRAINT vacante_cargo_id_fkey FOREIGN KEY (cargo_id) REFERENCES public.cargo(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.vacante
    ADD CONSTRAINT vacante_departamento_id_fkey FOREIGN KEY (departamento_id) REFERENCES public.departamento(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.vacante
    ADD CONSTRAINT vacante_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.vacante_habilidad
    ADD CONSTRAINT vacante_habilidad_habilidad_id_fkey FOREIGN KEY (habilidad_id) REFERENCES public.habilidad(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.vacante_habilidad
    ADD CONSTRAINT vacante_habilidad_vacante_id_fkey FOREIGN KEY (vacante_id) REFERENCES public.vacante(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.vacante
    ADD CONSTRAINT vacante_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;

