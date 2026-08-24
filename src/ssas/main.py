from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ssas.core.api.router import api_router
from ssas.core.tenancy.middleware import EmpresaContextMiddleware
from ssas.infrastructure.database.session import dispose_engine

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(
    title="SSAS RRHH API",
    description="API backend para la plataforma SSAS RRHH.",
    version="0.1.0",
    lifespan=lifespan,
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
    return {"message": "Backend SSAS RRHH"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
