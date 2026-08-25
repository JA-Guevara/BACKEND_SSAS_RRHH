"""Autorización del área de plataforma.

No hay un sistema de autenticación paralelo: se reutiliza el mismo ``CurrentUser`` que
el resto de la API. Lo que distingue a un administrador de plataforma es su
``empresa_id IS NULL`` y los permisos ``platform:*`` que traen sus roles globales.
"""

from ssas.core.security.dependencies import CurrentUser, require_platform_permission

CurrentPlatformAdmin = CurrentUser

__all__ = ["CurrentPlatformAdmin", "CurrentUser", "require_platform_permission"]
