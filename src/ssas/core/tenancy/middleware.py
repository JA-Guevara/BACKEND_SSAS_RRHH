from collections.abc import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from ssas.auth.domain.exceptions import AuthError
from ssas.core.security.jwt import JWTService
from ssas.core.tenancy.context import clear_current_empresa_id, set_current_empresa_id

PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/password/forgot",
        "/api/v1/auth/password/reset",
        "/api/v1/auth/email/verification/resend",
        "/api/v1/auth/email/verify",
    }
)

# /api/v1/platform ya NO se excluye: sus rutas pasan por el mismo middleware y las
# protege el mismo sistema de permisos que el resto de la API.
PUBLIC_PATH_PREFIXES: tuple[str, ...] = ("/docs/",)


class EmpresaContextMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        public_paths: Iterable[str] = PUBLIC_PATHS,
        public_path_prefixes: Iterable[str] = PUBLIC_PATH_PREFIXES,
    ) -> None:
        super().__init__(app)
        self.public_paths = frozenset(public_paths)
        self.public_path_prefixes = tuple(public_path_prefixes)
        self.token_service = JWTService()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            return await call_next(request)

        token = self._extract_bearer_token(request)
        if token is None:
            return self._unauthorized("Autenticación requerida")

        try:
            payload = self.token_service.decode_token(token, expected_type="access")
        except AuthError:
            return self._unauthorized("Token inválido")

        empresa_id = payload.get("tid")
        if empresa_id is None:
            # Administrador de plataforma: no hay empresa que fijar en el contexto.
            return await call_next(request)
        if not isinstance(empresa_id, str) or not empresa_id.strip():
            return self._unauthorized("El token no contiene una empresa válida")

        context_token = set_current_empresa_id(empresa_id)
        try:
            return await call_next(request)
        finally:
            clear_current_empresa_id(context_token)

    def _is_public_path(self, path: str) -> bool:
        return path in self.public_paths or any(
            path.startswith(prefix) for prefix in self.public_path_prefixes
        )

    @staticmethod
    def _extract_bearer_token(request: Request) -> str | None:
        authorization = request.headers.get("Authorization")
        if authorization is None:
            return None

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return None
        return token.strip()

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"detail": detail})
