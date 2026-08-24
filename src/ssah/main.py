from fastapi import FastAPI

from ssah.core.api.router import api_router
from ssah.core.tenancy.middleware import EmpresaContextMiddleware

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="SSAH RRHH API",
    description="API backend para la plataforma SSAH RRHH.",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Autenticacion y sesion"},
        {"name": "usuarios", "description": "Gestion de usuarios por empresa"},
        {"name": "roles", "description": "Roles y permisos"},
        {"name": "empresa", "description": "Configuracion de empresa"},
        {"name": "bitacora", "description": "Auditoria del sistema"},
    ],
)
app.add_middleware(EmpresaContextMiddleware)
app.include_router(api_router, prefix=API_V1_PREFIX)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Backend SSAH RRHH"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
