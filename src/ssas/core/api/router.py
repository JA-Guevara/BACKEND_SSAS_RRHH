from fastapi import APIRouter

from ssas.auth.infrastructure.http.router import router as auth_router
from ssas.bitacora.infrastructure.http.router import router as bitacora_router
from ssas.platform.infrastructure.http.router import router as platform_router
from ssas.roles.infrastructure.http.router import router as roles_router
from ssas.usuarios.infrastructure.http.router import router as usuarios_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(bitacora_router)
api_router.include_router(platform_router)
api_router.include_router(roles_router)
api_router.include_router(usuarios_router)
