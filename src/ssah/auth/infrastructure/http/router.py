from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from ssah.auth.application.use_cases.get_current_user import GetCurrentUser
from ssah.auth.application.use_cases.login_user import LoginUser
from ssah.auth.application.use_cases.logout_user import LogoutUser
from ssah.auth.application.use_cases.refresh_token import RefreshToken
from ssah.auth.application.use_cases.register_user import RegisterUser
from ssah.auth.application.use_cases.request_password_reset import RequestPasswordReset
from ssah.auth.application.use_cases.reset_password import ResetPassword
from ssah.auth.domain.exceptions import (
    AuthError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ssah.auth.infrastructure.http.schemas import (
    ForgotPasswordResponseSchema,
    ForgotPasswordSchema,
    LoginSchema,
    MessageSchema,
    RefreshTokenSchema,
    RegisterSchema,
    ResetPasswordSchema,
    TokenPairSchema,
    UserSchema,
)
from ssah.auth.infrastructure.persistence.repositories.auth_token_repository import (
    SqlAlchemyAuthTokenRepository,
)
from ssah.auth.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from ssah.auth.infrastructure.security.jwt_service import JWTService
from ssah.auth.infrastructure.security.password_hasher import BcryptPasswordHasher
from ssah.config.settings import settings
from ssah.infrastructure.database.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)
token_service = JWTService()
password_hasher = BcryptPasswordHasher()


def _raise_http_auth_error(exc: AuthError) -> None:
    if isinstance(exc, UserAlreadyExistsError):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, UserNotFoundError):
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


def get_access_token_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    try:
        payload = token_service.decode_token(credentials.credentials, expected_type="access")
    except AuthError as exc:
        _raise_http_auth_error(exc)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=401, detail="Token inválido")
    return subject


@router.get("/health")
async def auth_health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await RegisterUser(_user_repository(session), password_hasher).execute(
            **request.model_dump()
        )
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.post("/login", response_model=TokenPairSchema)
async def login_user(
    request: LoginSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await LoginUser(
            _user_repository(session),
            password_hasher,
            token_service,
            _token_repository(session),
        ).execute(**request.model_dump())
    except AuthError as exc:
        _raise_http_auth_error(exc)


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
    session: AsyncSession = Depends(get_session),
):
    try:
        await LogoutUser(token_service, _token_repository(session)).execute(request.refresh_token)
        return {"message": "Sesión cerrada correctamente"}
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.get("/me", response_model=UserSchema)
async def current_user(
    user_id: str = Depends(get_access_token_subject),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await GetCurrentUser(_user_repository(session)).execute(user_id)
    except AuthError as exc:
        _raise_http_auth_error(exc)


@router.post("/password/forgot", response_model=ForgotPasswordResponseSchema)
async def forgot_password(
    request: ForgotPasswordSchema,
    session: AsyncSession = Depends(get_session),
):
    raw_token = await RequestPasswordReset(
        _user_repository(session),
        _token_repository(session),
        token_service,
        settings.app_password_reset_expire_minutes,
    ).execute(str(request.email))
    return {
        "message": "Si el correo existe, se generó un enlace de recuperación",
        "reset_token": raw_token
        if settings.app_env == "development" and settings.app_debug
        else None,
    }


@router.post("/password/reset", response_model=MessageSchema)
async def reset_password(
    request: ResetPasswordSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        await ResetPassword(
            _user_repository(session),
            _token_repository(session),
            token_service,
            password_hasher,
        ).execute(request.token, request.new_password)
        return {"message": "Contraseña restablecida correctamente"}
    except AuthError as exc:
        _raise_http_auth_error(exc)
