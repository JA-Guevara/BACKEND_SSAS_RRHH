class EmpresaError(Exception):
    """Base exception for company configuration business errors."""


class ParametroLegalNotFoundError(EmpresaError):
    pass


class ParametroValorNotFoundError(EmpresaError):
    pass


class ParametroValorInvalidoError(EmpresaError):
    pass


class ParametroVigenciaInvalidaError(EmpresaError):
    pass