class ParametroLegalError(Exception):
    """Error base del módulo de parámetros legales."""


class ParametroLegalNotFoundError(ParametroLegalError):
    """El periodo solicitado no existe o pertenece a otra empresa."""


class ParametroLegalOverlapError(ParametroLegalError):
    """El periodo de vigencia se solapa con otro ya registrado."""


class ParametroLegalRangeError(ParametroLegalError):
    """Rango de fechas o porcentajes inválido."""


class ParametroLegalPercentError(ParametroLegalError):
    """Un porcentaje está fuera del rango permitido (0 a 100)."""