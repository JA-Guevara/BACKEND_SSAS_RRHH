from contextvars import ContextVar, Token

from fastapi import HTTPException, status

_current_empresa_id: ContextVar[str | None] = ContextVar("current_empresa_id", default=None)


def set_current_empresa_id(empresa_id: str) -> Token[str | None]:
    return _current_empresa_id.set(empresa_id)


def get_current_empresa_id() -> str | None:
    return _current_empresa_id.get()


def require_empresa_context() -> str:
    empresa_id = get_current_empresa_id()
    if empresa_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empresa no encontrada en el contexto de la petición",
        )
    return empresa_id


def clear_current_empresa_id(token: Token[str | None]) -> None:
    _current_empresa_id.reset(token)