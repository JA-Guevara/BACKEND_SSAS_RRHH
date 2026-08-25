from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ssas.config.settings import settings
from ssas.core.api.openapi import (
    TAG_AUDIT,
    TAG_AUTH,
    TAG_COMPANIES,
    TAG_ROLES,
    TAG_USERS,
)
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
    description=(
        "Backend multiempresa para la administración de recursos humanos.\n\n"
        "## Alcance de seguridad\n"
        "- **Plataforma:** una cuenta sin empresa administra recursos globales y puede "
        "seleccionar una empresa cuando el endpoint lo permita.\n"
        "- **Empresa:** cada usuario queda limitado al `empresa_id` incluido en su token.\n"
        "- Las operaciones protegidas requieren `Authorization: Bearer <access_token>`."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": TAG_AUTH,
            "description": "Inicio y cierre de sesión, tokens, contraseñas y correo.",
        },
        {
            "name": TAG_USERS,
            "description": "Administración de usuarios globales y usuarios por empresa.",
        },
        {
            "name": TAG_COMPANIES,
            "description": "Aprovisionamiento, consulta y estado de las empresas.",
        },
        {
            "name": TAG_ROLES,
            "description": "Roles por alcance y asignación de permisos RBAC.",
        },
        {
            "name": TAG_AUDIT,
            "description": "Consulta de eventos registrados por módulo, usuario y empresa.",
        },
    ],
    license_info={"name": "MIT", "identifier": "MIT"},
)
app.add_middleware(EmpresaContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def read_root() -> dict[str, str]:
    return {"message": "Backend SSAS RRHH"}


@app.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
