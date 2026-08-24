from enum import StrEnum


class AuditModule(StrEnum):
    AUTH = "AUTH"
    USUARIOS = "USUARIOS"
    ROLES = "ROLES"
    EMPRESAS = "EMPRESAS"
    BITACORA = "BITACORA"
    RECLUTAMIENTO = "RECLUTAMIENTO"
    SELECCION = "SELECCION"
    PERSONAL = "PERSONAL"
    PLANILLA = "PLANILLA"
    ASISTENCIA = "ASISTENCIA"
    CAPACITACION = "CAPACITACION"
    REPORTES = "REPORTES"


class AuditAction(StrEnum):
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    ASSIGN = "ASSIGN"
    UNASSIGN = "UNASSIGN"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ERROR = "ERROR"


def audit_level(action: str) -> str:
    if action == AuditAction.ERROR:
        return "CRITICAL"
    if action in {
        AuditAction.LOGIN_FAILED,
        AuditAction.DELETE,
        AuditAction.DEACTIVATE,
        AuditAction.UNASSIGN,
        AuditAction.REJECT,
    }:
        return "WARNING"
    return "INFO"
