class BitacoraError(Exception):
    """Base exception for bitacora domain errors."""


class AuditLogNotFoundError(BitacoraError):
    pass
