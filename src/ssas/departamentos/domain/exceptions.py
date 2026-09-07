class DepartamentoError(Exception):
    """Error base del modulo departamentos."""


class DepartamentoAlreadyExistsError(DepartamentoError):
    pass


class DepartamentoNotFoundError(DepartamentoError):
    pass


class DepartamentoInUseError(DepartamentoError):
    pass
