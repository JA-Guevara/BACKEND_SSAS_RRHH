# DOC-02 · Casos de prueba funcionales (Caja negra) — Sprint 2

> Reemplaza las tablas vacías de "2.3 Pruebas - Sprint 2" del perfil.
> Todos los casos corresponden a pruebas realmente ejecutadas (`QA-01`…`QA-04`) y son rastreables a
> `tests/integration/test_sprint2_selection.py` y al flujo de punta a punta `test_flujo_completo_cu13_a_cu19`.
> Al menos un caso negativo por caso de uso (denotados con **Negativo**).

## CU-13 · Análisis de CV con IA y extracción de datos

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP13-01 | Postulación `ACTIVA` con CV en PDF y vacante con 3 habilidades | `POST /api/v1/postulaciones/{id}/analisis-cv` | **201**. `puntaje_afinidad` en [0,100], `habilidades_detectadas` y `habilidades_faltantes` pobladas, `modelo_usado` = `extraccion-local-v1` (sin conectividad), `anios_experiencia_detectados` = años del CV |
| CP13-02 | Postulación cuyo postulante no tiene CV adjunto | Mismo endpoint | **409** "El postulante no tiene CV adjunto". No se crea registro en `analisis_cv` |
| CP13-03 | **Negativo**: postulación en estado `DESCARTADA` | Mismo endpoint | **409** "Solo se analizan postulaciones activas" |
| CP13-04 | **Negativo**: proveedor Gemini responde 502 (indisponible) en modo `auto` | Mismo endpoint | **201**, degradación transparente al proveedor local; el puntaje no cambia y `modelo_usado` documenta el origen |

## CU-14 · Ranking de candidatos

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP14-01 | Vacante con 3 postulaciones (una con `puntaje_ia`) | `GET /api/v1/vacantes/{id}/ranking?orden=ia` | **200**. `total` = 3, primero el de mayor afinidad; el candidato sin análisis queda último con `puntaje_ia` = `null` |
| CP14-02 | Vacante con evaluaciones registradas | `GET /api/v1/vacantes/{id}/ranking` | **200**. El puntaje combinado incluye IA + manual + entrevistas + evaluaciones (p. ej. `puntaje_evaluaciones` = 80) |
| CP14-03 | Postulaciones de la misma vacante | `GET …/ranking?orden=manual&limit=1` | **200**. Paginación correcta (`total` = 3, `items` = 1) y orden por puntaje manual |
| CP14-04 | **Negativo**: usuario de otra empresa consulta el ranking | Mismo endpoint | **404** (no se filtra información de otro tenant) |
| CP14-05 | **Negativo**: rol sin permiso `entrevistas:ver` usa `orden=entrevistas` | Mismo endpoint | **403** al intentar exponer puntajes derivados |

## CU-15 · Gestión de entrevistas y confirmación pública

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP15-01 | Entrevista virtual futura, entrevistador del mismo tenant | `POST /api/v1/entrevistas` | **201**, estado `PROGRAMADA` |
| CP15-02 | Entrevista `PROGRAMADA` futura y código de seguimiento válido | `POST /api/v1/publico/postulaciones/{codigo}/entrevista/confirmar` | **200**, estado `CONFIRMADA` (sin autenticación) |
| CP15-03 | Cambio de estado a `CANCELADA` | `PATCH /api/v1/entrevistas/{id}/estado` | **200**, no se puede volver a `CONFIRMADA` (ver CP15-05) |
| CP15-04 | **Negativo**: entrevista ya `CANCELADA` | `POST …/entrevista/confirmar` | **404**: el portal solo expone entrevistas `PROGRAMADA`/`CONFIRMADA` futuras |
| CP15-05 | **Negativo**: transición `CANCELADA` → `CONFIRMADA` | `PATCH …/estado` | **409** transición inválida |
| CP15-06 | **Negativo**: `entrevistador_id` de otra empresa | `POST /api/v1/entrevistas` | **422** (responsable fuera del alcance de la empresa) |

## CU-16 · Resultados y evaluaciones técnicas y psicotécnicas

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP16-01 | Evaluación `TECNICA`, `puntaje` 15 / `puntaje_maximo` 20 | `POST /api/v1/postulaciones/{id}/evaluaciones` | **201**, `evaluador_id` = usuario autenticado, puntaje persistido (`18.00` tras actualización) |
| CP16-02 | Entrevista ya realizada (fecha pasada) | `PATCH /api/v1/entrevistas/{id}/resultado` | **200**, estado pasa a `REALIZADA` con `puntaje` y `recomendacion` |
| CP16-03 | **Negativo**: `puntaje` 21 > `puntaje_maximo` 20 | `POST …/evaluaciones` | **422** validación de rango |
| CP16-04 | **Negativo**: `evaluador_id` de otra empresa | `POST …/evaluaciones` | **403** |
| CP16-05 | **Negativo**: se intenta registrar resultado antes de la fecha de la entrevista | `PATCH …/resultado` | **409** |

## CU-17 · Comparar finalistas

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP17-01 | Dos postulaciones de la misma vacante | `POST /api/v1/vacantes/{id}/comparar` | **200** con el detalle de cada candidato y su ranking |
| CP17-02 | Cuatro postulaciones (máximo permitido) | Mismo endpoint | **200** |
| CP17-03 | **Negativo**: una postulación pertenece a otra vacante | Mismo endpoint | **422** |
| CP17-04 | **Negativo**: la misma postulación repetida dos veces | Mismo endpoint | **422** |

## CU-18 · Gestionar banco de talentos

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP18-01 | Postulante propio | `PATCH /api/v1/postulantes/{id}/banco-talento` `{ "en_banco_talento": true }` | **200**, `en_banco_talento` = `true` |
| CP18-02 | Postulante propio + vacante | `POST /api/v1/postulantes/{id}/postulaciones` | **201** con respuesta tipada `AsociacionResponse` |
| CP18-03 | **Negativo**: postulante de otra empresa | `PATCH …/banco-talento` | **404** (no se revela la existencia del recurso) |

## CU-19 · Contratación y alta de empleado

| ID | Entrada | Proceso | Salida esperada |
|---|---|---|---|
| CP19-01 | Postulación `ACTIVA`, código de empleado libre | `POST /api/v1/postulaciones/{id}/contratar` | **201**, empleado creado, `postulacion.empleado_id` apunta a él, estado `CONTRATADA`, vacante `CERRADA` |
| CP19-02 | Mismo código de empleado ya usado en la empresa | Mismo endpoint | **409** por `uq_empleado_empresa_codigo` |
| CP19-03 | Reintento de contratación idempotente de la misma postulación | Mismo endpoint | **201** y devuelve el mismo `id` de empleado (no duplica) |
| CP19-04 | **Negativo**: fallo de auditoría durante la transacción | Mismo endpoint | **409** y *rollback* total: sin empleado, postulación `ACTIVA`, vacante `PUBLICADA` |
| CP19-05 | Empleado creado por CP19-01 | `GET /api/v1/empleados` | **200**, el empleado aparece en el listado de la empresa |

## Trazabilidad

- Flujo de punta a punta CU-13 → CU-19: `tests/integration/test_sprint2_selection.py::test_flujo_completo_cu13_a_cu19` (QA-04).
- Aislamiento multiempresa: `test_sql_tenant_isolation_and_effective_permissions`.
- Concurrencia/locks reales de PostgreSQL: `test_concurrent_requests_serialize_real_sql_locks`.
- Unitarios de extracción local: `tests/unit/test_extraccion_local.py`; respaldo: `test_analisis_cv_respaldo.py`.