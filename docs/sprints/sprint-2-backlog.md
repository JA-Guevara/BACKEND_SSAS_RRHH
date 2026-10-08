# DOC-05 · Sprint backlog y evidencias del Sprint 2

> Reemplaza la tabla declarativa del Sprint 2 (que afirmaba 25 tareas T2-01 a T2-25) por una tabla
> **trazada contra commits reales** de ambos repos.
> Nombres de las tareas tomados de `sprint2.xlsx` (pestaña del Sprint 2).
> Trazabilidad verificada con `git log --all --date=short` en `BACKEND_SSAS_RRHH` y `FRONTEND_SSAS_RRHH`.
>
> De los 25 IDs, **solo 5 aparecen literalmente** en los mensajes de commit (T2-11, T2-13, T2-15,
> T2-17, T2-25). Las demás filas se trazan por el contenido del commit que implementa la tarea.

## Tabla del Sprint 2

| ID | Tarea | Historia | Responsable | Commit(s) que la cierran | Estado |
|---|---|---|---|---|---|
| T2-01 | Modelos entrevista y evaluación + migración | HU-08 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-02 | Endpoints de entrevistas | HU-08 | Jordi-Roma | `131e82b`, `f19396d` (backend) | Hecho |
| T2-03 | Endpoints de evaluaciones | HU-08 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-04 | Modelo `analisis_cv` + extracción de texto del CV | HU-07 | Jordi-Roma | `9f75017`, `61b4521`, `c650f82` (backend) | Hecho |
| T2-05 | Servicio IA: puntaje de afinidad CV vs vacante | HU-07 | Jordi-Roma / Jose A. Guevara | `010d00b`, `a782194` (backend) | Hecho |
| T2-06 | Endpoint de ranking de candidatos | HU-07 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-07 | Endpoint contratar: postulante a empleado (transaccional) | HU-10 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-08 | Banco de talentos | HU-06 | Jordi-Roma | `d3d5048`, `131e82b` (backend) | Hecho |
| T2-09 | Comparador de finalistas | HU-06 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-10 | OpenAPI + Postman del Sprint 2 | — | Jose A. Guevara | `e133c73`, `ea9d23f`, `dd15350` (backend) | Hecho |
| T2-11 | Agenda de entrevistas | HU-08 | Sergio Oscar | `36cb628` (frontend) | Hecho |
| T2-12 | Registro de resultados y evaluaciones | HU-08 | Jordi-Roma | `131e82b` (backend) | Hecho |
| T2-13 | Ranking IA en el tablero | HU-07 | Sergio Oscar | `e337fcb` (frontend) | Hecho |
| T2-14 | Comparador de finalistas (web) | HU-06 | Jordi-Roma | `5ff312a` (frontend, merge del módulo) | Hecho |
| T2-15 | Flujo Contratar (conversión a empleado) | HU-10 | Sergio Oscar | `6783433` (frontend) | Hecho |
| T2-16 | Banco de talentos (web) | HU-06 | Jordi-Roma | `5ff312a` (frontend, merge del módulo) | Hecho |
| T2-17 | Historial del postulante | HU-06 | Sergio Oscar | `36cf327` (frontend) + `131e82b` (backend) | Hecho |
| T2-18 | Línea de tiempo de la postulación (móvil) | HU-09 | — | — | **Fuera de alcance (DOC-04)** |
| T2-19 | Confirmar entrevista desde el móvil | HU-09 | — | Equivalente web: `9b5921c`, `f19396d` | **Fuera de alcance (DOC-04)** |
| T2-20 | Ranking móvil del reclutador (solo lectura) | HU-09 | — | — | **Fuera de alcance (DOC-04)** |
| T2-21 | Pruebas del Sprint 2 + reporte | HU-07, HU-10 | Lorgio09 / Jose A. Guevara | `324654a`, `61890ae` (backend) + vitest (frontend) | Hecho |
| T2-22 | Documentar el Sprint 2 en el capítulo 4 | — | Jose A. Guevara | `c76f166` → `docs/sprints/sprint-2-seleccion.md` | Hecho |
| T2-23 | Demo del Sprint Review 2 | — | Jose A. Guevara | `docs/SPRINT_2_DESPLIEGUE_Y_DEMO.md` + colección Postman | Hecho |
| T2-24 | Deploy y verificación en Railway | — | Jose A. Guevara | — | **Pendiente (R-08)** |
| T2-25 | Datos de demostración del Sprint | — | Sergio Oscar | `30494e9` (frontend) + `scripts/cargar_sprint2_demo.py` (backend) | Hecho |

## Resumen

- **19 tareas entregadas** y trazadas a commits reales.
- **3 tareas móviles** (T2-18, T2-19, T2-20) reclasificadas como fuera de alcance por la decisión
  DOC-04; el equivalente web de T2-19 sí está entregado.
- **1 tarea pendiente** (T2-24, deploy en Railway) hasta cerrar la verificación del entorno desplegado.
- Los IDs de frontend llevan a commits verificables en `FRONTEND_SSAS_RRHH`; los de backend a `BACKEND_SSAS_RRHH`.

## Cómo reproducir la trazabilidad

```bash
git log --all --since=2026-09-01 --date=short --pretty=format:'%h|%ad|%an|%s'
git log --all | grep -E 'T2-[0-9]+'
```