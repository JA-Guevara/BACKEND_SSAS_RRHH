class UsuarioError(Exception):
    """Base exception for user management business errors."""


class UsuarioNotFoundError(UsuarioError):
    pass


class UsuarioAlreadyExistsError(UsuarioError):
    pass


class UsuarioWithoutRoleError(UsuarioError):
    pass


class InvalidRoleForEmpresaError(UsuarioError):
    pass


class LastAdminCannotBeDisabledError(UsuarioError):
    pass