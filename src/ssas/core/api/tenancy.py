"""Resolución del inquilino objetivo de una petición.

La regla de aislamiento se escribe una sola vez. Tener dos implementaciones con
comportamientos distintos ante el mismo caso es como se filtran datos entre
empresas en una plataforma multi-tenant.
"""

from fastapi import HTTPException

from ssas.core.security.dependencies import CurrentUser


def resolver_empresa(user: CurrentUser, requested: str | None) -> str:
    if user.es_plataforma:
        if requested is None:
            raise HTTPException(status_code=422, detail="Debe indicar empresa_id")
        return requested
    if user.empresa_id is None:
        raise HTTPException(status_code=403, detail="No tienes una empresa asignada")
    if requested and requested != user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes operar sobre otra empresa")
    return user.empresa_id