class AuthError(Exception):
    """Base exception for auth domain errors."""


class UserAlreadyExistsError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class TokenExpiredError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class InactiveUserError(AuthError):
    pass


class UserNotFoundError(AuthError):
    pass


class InvalidPasswordError(AuthError):
    pass


class AccountLockedError(AuthError):
    pass


class EmailNotVerifiedError(AuthError):
    pass


class EmailDeliveryError(AuthError):
    pass
