# DOC-01 · Script DDL del perfil de proyecto

> Reemplaza el script de la sección **2.1.2 Diseño de datos** del perfil.
> Fuente: `pg_dump --schema-only` sobre la base local, la misma que corre en producción
> (`alembic current` = `20261005_0009 (head)`).
>
> - Dump crudo generado por pg_dump: `docs/ddl/esquema_pg_dump_raw.sql`
> - Salida limpia (sin `SET`, `SELECT pg_catalog…`, `\restrict` ni cabeceras de pg_dump): `docs/ddl/esquema_real.sql`

## 1. Diferencias entre el script del documento y la base real

Todas verificadas contra `docs/ddl/esquema_real.sql` (el ORM y la base coinciden).

| Tabla | El documento dice | La base real tiene | Acción |
|---|---|---|---|
| `postulacion` | `calificacion_ia` | `puntaje_ia` | Corregir: el nombre real es `puntaje_ia` |
| `postulacion` | sin `empleado_id` | `empleado_id UUID UNIQUE REFERENCES empleado(id)` | Agregar |
| `postulante` | sin `cv_texto` | `cv_texto TEXT` | Agregar |
| `postulante_habilidad` | sin `detectado_por_ia` | `detectado_por_ia BOOLEAN` | Agregar |
| `entrevista` | `fecha DATE` + `hora TIME` | `fecha_hora TIMESTAMPTZ` | Corregir |
| `entrevista` | sin `tipo`/`puntaje`/`recomendacion` | `tipo`, `puntaje`, `recomendacion` | Agregar |
| `evaluacion` | sin `nombre`/`archivo_url` | `nombre`, `archivo_url` | Agregar |
| `analisis_cv` | sin `habilidades_faltantes`/`modelo_usado` | `habilidades_faltantes`, `modelo_usado` | Agregar |
| `etapa_reclutamiento` | sin `es_contratado` | `es_contratado BOOLEAN` | Agregar |
| `empleado` | `nit_ci` | `ci` + `ci_expedido` | Corregir: no existe la columna `nit_ci` |

## 2. Cantidad de tablas

La base real tiene **39 tablas** (38 de aplicación + `alembic_version` de control de migraciones),
no 36. Las tablas por encima de las 36 del documento son los módulos de plataforma construidos
además del alcance declarado.

## 3. Tablas de infraestructura de plataforma (justificación documental)

Estas tablas no corresponden a un caso de uso del alcance y **deben quedar con una nota explícita**
de que son infraestructura de plataforma, o con el CU/RF que las justifique:

| Tabla | Módulo | Origen |
|---|---|---|
| `plan_suscripcion`, `suscripcion` | `empresas` | Cobro SaaS con Stripe |
| `plan_modulo`, `stripe_evento` | `suscripciones` | Cobro SaaS con Stripe |
| `respaldo` | `respaldos` | Respaldo y restauración |
| `conocimiento_articulo`, `conocimiento_fragmento` | `ayuda` | Chatbot (CU-31/CU-32, Sprint 4) |

## 4. Cómo usarlo

1. Abrir `docs/ddl/esquema_real.sql`.
2. Reemplazar el bloque SQL de la sección 2.1.2 por el contenido, conservando la organización por
   módulos y los comentarios en español del script original.
3. Aplicar las correcciones de la tabla del punto 1 si el script se transcribe a mano.
4. Añadir la nota del punto 3 para las tablas de plataforma.