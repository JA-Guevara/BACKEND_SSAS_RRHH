# Documentación archivada

Estos archivos se retiraron el 2026-09-07 porque estaban **redundantes u obsoletos**.
Se conservan por trazabilidad; se pueden borrar sin pérdida de información vigente.

| Archivo | Motivo |
|---|---|
| `OPENAPI_VERSIONADO_SPRINT1.md` | Duplicaba `arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md`, que es más completo (130 líneas vs 40). Su parte útil —el alcance del Sprint 1 y los pendientes— quedó cubierta con datos reales en `01_ESTADO_PROYECTO.md` y `03_BACKLOG_IMPLEMENTACION.md`. |
| `ANALISIS_Y_PROPUESTA_BACKEND.md` | Auditoría del 18/08/2026 sobre una estructura anterior al paquete `ssas` y a la unificación de plataforma. Sus recomendaciones ya están aplicadas; el texto describe tablas y rutas que no existen. |
| `schema_sprint0_sprint1.sql` | Esquema escrito a mano que competía con Alembic como fuente de verdad, y ya desincronizado: documentaba 23 tablas cuando el ORM define 19. Cuatro de ellas (`parametro_legal`, `parametro_valor`, `plan_suscripcion`, `suscripcion`) no existen ni en las migraciones ni en el código. El esquema real lo define `migrations/versions/`. |

Para obtener el esquema vigente:

```bash
alembic upgrade head
pg_dump --schema-only -n public "$DATABASE_URL"
```
