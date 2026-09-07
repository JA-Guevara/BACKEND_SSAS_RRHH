class PostulacionError(Exception):
    """Error base del modulo postulaciones."""


class VacanteNoDisponibleError(PostulacionError):
    pass


class EtapaInicialNoConfiguradaError(PostulacionError):
    pass


class PostulacionDuplicadaError(PostulacionError):
    pass


class PostulacionNotFoundError(PostulacionError):
    pass


class CvInvalidoError(PostulacionError):
    pass
