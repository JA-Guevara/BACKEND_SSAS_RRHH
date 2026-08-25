class PlatformError(Exception):
    """Error base del módulo de plataforma."""


class PlatformNotFoundError(PlatformError):
    pass


class PlatformConflictError(PlatformError):
    pass


class PlatformValidationError(PlatformError):
    pass
