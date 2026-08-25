"""El módulo platform ya no tiene modelos propios.

Los administradores de la plataforma son filas de ``usuario`` con ``empresa_id IS NULL``,
sus tokens viven en ``refresh_token`` y sus eventos en ``bitacora`` con ``empresa_id IS NULL``.
"""

__all__: list[str] = []
