class PlatformError(Exception):
    """Error base del módulo de plataforma."""


class PlatformNotFoundError(PlatformError):
    pass


class PlatformConflictError(PlatformError):
    pass


class PlatformValidationError(PlatformError):
    pass


class RolBasePermisoDesconocidoError(PlatformError):
    """Un rol base se definió con un permiso que no existe en el catálogo.

    Se lanza en vez de descartar el código en silencio: un rol base que queda sin
    permisos por una errata pasa desapercibido hasta que el cliente reporta que su
    reclutador no puede hacer nada.
    """
