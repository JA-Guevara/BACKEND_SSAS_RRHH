from fastapi import APIRouter

from ssah.auth.infrastructure.http.router import router as auth_router
from ssah.bitacora.infrastructure.http.router import router as bitacora_router
from ssah.empresas.infrastructure.http.router import router as empresas_router
from ssah.roles.infrastructure.http.router import router as roles_router
from ssah.usuarios.infrastructure.http.router import router as usuarios_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(bitacora_router)
api_router.include_router(empresas_router)
api_router.include_router(roles_router)
api_router.include_router(usuarios_router)