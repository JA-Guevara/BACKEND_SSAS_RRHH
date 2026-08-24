import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.application.use_cases.get_current_user import GetCurrentUser
from ssas.auth.application.use_cases.login_user import LoginUser
from ssas.auth.application.use_cases.logout_user import LogoutUser
from ssas.auth.application.use_cases.refresh_token import RefreshToken
from ssas.auth.application.use_cases.request_password_reset import RequestPasswordReset
from ssas.auth.application.use_cases.reset_password import ResetPassword
from ssas.auth.domain.exceptions import (
    AuthError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidTokenError,
    TokenExpiredError,
    UserNotFoundError,
)
from ssas.auth.infrastructure.http.schemas import (
    ForgotPasswordResponseSchema,
    ForgotPasswordSchema,
    LoginSchema,
    MessageSchema,
    RefreshTokenSchema,
    ResetPasswordSchema,
    TokenPairSchema,
    UserSchema,
)
from ssas.auth.infrastructure.persistence.repositories.auth_token_repository import (
    SqlAlchemyAuthTokenRepository,
)
from ssas.auth.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from ssas.auth.infrastructure.security.jwt_service import JWTService
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.bitacora.application.events.auth_events import AuthEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.core.security.dependencies import CurrentUser
from ssas.core.security.dependencies import get_current_user as get_authenticated_user
from ssas.infrastructure.database.session import AsyncSessionLocal, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
token_service = JWTService()
password_hasher = Argon2PasswordHasher()


def _raise_http_auth_error(exc: AuthError) -> None:
    if isinstance(exc, UserNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, InvalidPasswordError):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(
        exc,
        (InvalidCredentialsError, InvalidTokenError, TokenExpiredError, InactiveUserError),
    ):
        code = status.HTTP_401_UNAUTHORIZED
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=str(exc)) from exc


def _user_repository(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def _token_repository(session: AsyncSession) -> SqlAlchemyAuthTokenRepository:
    return SqlAlchemyAuthTokenRepository(session)


def _events(session: AsyncSession) -> AuthEvents:
    return AuthEvents(RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)))


def _request_context(request: Request) -> dict[str, str | None]:
    return {
        "source_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


async def _record_failed_login(user, request: Request) -> None:
    """Persiste el intento fallido aunque la petición principal termine con HTTP 401."""
    if user is None or not user.empresa_id:
        return
    try:
        async with AsyncSessionLocal() as audit_session:
            await _events(audit_session).login_failed(
                empresa_id=user.empresa_id,
                user_id=user.id,
                actor_label=user.email,
                **_request_context(request),
            )
            await audit_session.commit()
    except Exception:
        logger.exception("No se pudo registrar un intento fallido de inicio de sesión")


@router.get("/health")
async def auth_health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/login", response_model=TokenPairSchema)
async def login_user(
    request: LoginSchema,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    repository = _user_repository(session)
    login = str(request.email) if request.email is not None else (request.username or "")
    try:
        result = await LoginUser(
            repository,
            password_hasher,
            token_service,
            _token_repository(session),
        ).execute(**request.model_dump())
    except AuthError as exc:
        user = await repository.get_by_login(login, request.empresa_slug)
        await _record_failed_login(user, http_request)
        _raise_http_auth_error(exc)
    payload = token_service.decode_token(result["access_token"], expected_type="access")
    await _events(session).login_success(
        empresa_id=str(payload["tid"]),
        user_id=str(payload["sub"]),
        actor_label=login,
        **_request_context(http_request),
    )
    return result


@router.post("/refresh", response_model=TokenPairSchema)
async def refresh_token(
    request: RefreshTokenSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await RefreshToken(
            token_service,
            _token_repository(session),
            _user_repository(session),
        ).execute(request.refresh_token)
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.post("/logout", response_model=MessageSchema)
async def logout_user(
    request: RefreshTokenSchema,
    http_request: Request,
    current_user: CurrentUser = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await LogoutUser(token_service, _token_repository(session)).execute(
            request.refresh_token,
            current_user.id,
            current_user.empresa_id,
        )
        await _events(session).logout(
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            **_request_context(http_request),
        )
        return {"message": "Sesión cerrada correctamente"}
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.get("/me", response_model=UserSchema)
async def current_user(
    current_user: CurrentUser = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await GetCurrentUser(_user_repository(session)).execute(
            current_user.id,
            current_user.empresa_id,
        )
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.post("/password/forgot", response_model=ForgotPasswordResponseSchema)
async def forgot_password(
    request: ForgotPasswordSchema,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    repository = _user_repository(session)
    raw_token = await RequestPasswordReset(
        repository,
        _token_repository(session),
        token_service,
        settings.app_password_reset_expire_minutes,
    ).execute(str(request.email), request.empresa_slug)
    if raw_token:
        user = await repository.get_by_login(str(request.email), request.empresa_slug)
        if user and user.empresa_id:
            await _events(session).password_reset_requested(
                empresa_id=user.empresa_id,
                user_id=user.id,
                actor_label=user.email,
                **_request_context(http_request),
            )
    return {
        "message": "Si el correo existe, se generó un enlace de recuperación",
        "reset_token": raw_token
        if settings.app_env == "development" and settings.app_debug
        else None,
    }


@router.post("/password/reset", response_model=MessageSchema)
async def reset_password(
    request: ResetPasswordSchema,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    token_repository = _token_repository(session)
    try:
        stored_token = await token_repository.get_active_password_reset_token(
            token_service.fingerprint(request.token)
        )
        await ResetPassword(
            _user_repository(session),
            token_repository,
            token_service,
            password_hasher,
        ).execute(request.token, request.new_password)
        if stored_token:
            await _events(session).password_reset_completed(
                empresa_id=stored_token.empresa_id,
                user_id=stored_token.user_id,
                **_request_context(http_request),
            )
        return {"message": "Contraseña restablecida correctamente"}
    except AuthError as exc:
        _raise_http_auth_error(exc)
