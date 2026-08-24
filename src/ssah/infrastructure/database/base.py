from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa compartida para todos los modelos ORM."""

    pass


def import_all_models() -> None:
    """Carga los modelos ORM para registrar relaciones y metadata en una Base única."""
    import ssah.auth.infrastructure.persistence.models.password_reset_token  # noqa: F401
    import ssah.auth.infrastructure.persistence.models.refresh_token  # noqa: F401
    import ssah.auth.infrastructure.persistence.models.user  # noqa: F401
    import ssah.bitacora.infrastructure.persistence.models.audit_log  # noqa: F401
    import ssah.empresas.infrastructure.persistence.models.empresa  # noqa: F401
    import ssah.empresas.infrastructure.persistence.models.parametro_legal  # noqa: F401
    import ssah.empresas.infrastructure.persistence.models.parametro_valor  # noqa: F401
    import ssah.empresas.infrastructure.persistence.models.plan_suscripcion  # noqa: F401
    import ssah.empresas.infrastructure.persistence.models.suscripcion  # noqa: F401
    import ssah.roles.infrastructure.persistence.models.permission  # noqa: F401
    import ssah.roles.infrastructure.persistence.models.role  # noqa: F401
    import ssah.roles.infrastructure.persistence.models.role_permission  # noqa: F401
    import ssah.roles.infrastructure.persistence.models.user_role  # noqa: F401