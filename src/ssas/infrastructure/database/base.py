from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa compartida para todos los modelos ORM."""



def import_all_models() -> None:
    """Carga los modelos ORM para registrar relaciones y metadata en una Base única."""
    import ssas.auth.infrastructure.persistence.models.email_verification_token
    import ssas.auth.infrastructure.persistence.models.password_reset_token
    import ssas.auth.infrastructure.persistence.models.refresh_token
    import ssas.auth.infrastructure.persistence.models.user
    import ssas.bitacora.infrastructure.persistence.models.audit_log
    import ssas.empresas.infrastructure.persistence.models.empresa
    import ssas.empresas.infrastructure.persistence.models.parametro_legal
    import ssas.empresas.infrastructure.persistence.models.parametro_valor
    import ssas.empresas.infrastructure.persistence.models.plan_suscripcion
    import ssas.empresas.infrastructure.persistence.models.suscripcion
    import ssas.platform.infrastructure.persistence.models.platform_admin
    import ssas.platform.infrastructure.persistence.models.platform_audit_log
    import ssas.platform.infrastructure.persistence.models.platform_refresh_token
    import ssas.roles.infrastructure.persistence.models.permission
    import ssas.roles.infrastructure.persistence.models.role
    import ssas.roles.infrastructure.persistence.models.role_permission
    import ssas.roles.infrastructure.persistence.models.user_role  # noqa: F401
