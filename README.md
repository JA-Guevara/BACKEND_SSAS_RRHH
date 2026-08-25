# SSAS RRHH — Backend

API REST multiempresa para la gestión de recursos humanos. Implementa autenticación, usuarios,
roles, permisos, empresas y bitácora de auditoría sobre una arquitectura modular.

## Estado actual

| Componente | Estado |
|---|---|
| FastAPI y OpenAPI | Operativo |
| PostgreSQL/Supabase | Conectado |
| Alembic | Migración inicial limpia `20260825_0001` preparada |
| Auth, bloqueo, verificación y recuperación | Implementado; requiere SMTP |
| Usuarios, roles y permisos | Implementado |
| Bitácora persistente | Implementado |
| Aislamiento multiempresa | Basado en `empresa_id` |
| Administración global SSAS | Superadministradores y empresas mediante RBAC |

## Tecnologías principales

- Python 3.12 y FastAPI
- SQLAlchemy 2 en modo asíncrono
- PostgreSQL con Psycopg 3
- Alembic para migraciones
- JWT y Argon2id para seguridad
- pytest y Ruff para calidad

## Inicio rápido

```powershell
git clone https://github.com/JA-Guevara/BACKEND_SSAS_RRHH.git
cd BACKEND_SSAS_RRHH

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

Copy-Item .env.example .env
# Configurar DATABASE_URL y APP_SECRET_KEY en .env

python -m uvicorn ssas.main:app --reload
```

Servicios locales:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Healthcheck: `http://127.0.0.1:8000/health`

## Comprobaciones

```powershell
python -m pytest
python -m ruff check src tests migrations scripts
python -m alembic current
python -m alembic check
```

## Documentación

La información detallada se mantiene organizada dentro de [`docs/`](docs/README.md):

- [Guía de desarrollo](docs/guias/GUIA_DESARROLLO.md)
- [Autenticación y gestión de usuarios](docs/guias/AUTH_Y_USUARIOS.md)
- [Administración global de SSAS](docs/guias/PLATFORM_ADMINISTRACION.md)
- [Arquitectura del backend](docs/arquitectura/ARQUITECTURA_BACKEND_FASTAPI.md)
- [Contrato OpenAPI y versionado](docs/arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md)
- [Análisis técnico](docs/analisis/ANALISIS_Y_PROPUESTA_BACKEND.md)
- [Evidencia del Sprint 0](docs/sprints/SPRINT_0_ADAPTACION_ORM.md)

## Seguridad

El archivo `.env` contiene secretos y está excluido de Git. Debe generarse desde `.env.example` y
nunca debe subirse al repositorio. Las credenciales expuestas deben rotarse inmediatamente.

## Licencia

Este proyecto se distribuye bajo la [licencia MIT](LICENSE).
