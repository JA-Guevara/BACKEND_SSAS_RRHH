"""Capa semántica del módulo de reportes.

Una única descripción de qué se puede consultar: fuentes, campos, tipos,
sensibilidad y permiso. El motor SQL y la interfaz se construyen sobre esta
capa; ninguna consulta debe construirse por fuera del catálogo.

Regla de plataforma: `Fuente.columna_tenant` no tiene valor por defecto. Es
imposible registrar una fuente sin declarar por dónde se aísla la empresa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# Permiso del módulo dueño del dato que se exige para ver la fuente.
# Los campos pueden exigir un permiso adicional en `Campo.permiso`.


class TipoCampo(StrEnum):
    TEXTO = "texto"
    NUMERO = "numero"
    FECHA = "fecha"
    BOOLEANO = "booleano"
    ENUM = "enum"


class Sensibilidad(StrEnum):
    """Determina quién puede ver la columna y si se enmascara/pide al exportar."""

    PUBLICO = "publico"
    INTERNO = "interno"
    PERSONAL = "personal"
    CONFIDENCIAL = "confidencial"


class Agregacion(StrEnum):
    CONTEO = "conteo"
    SUMA = "suma"
    PROMEDIO = "promedio"
    MINIMO = "minimo"
    MAXIMO = "maximo"


@dataclass(frozen=True)
class Campo:
    codigo: str
    etiqueta: str
    sql: str
    tipo: TipoCampo
    sensibilidad: Sensibilidad = Sensibilidad.PUBLICO
    permiso: str | None = None
    agrupable: bool = True
    agregable: bool = False
    valores: tuple[str, ...] = ()


@dataclass(frozen=True)
class Fuente:
    codigo: str
    etiqueta: str
    descripcion: str
    from_sql: str
    columna_tenant: str
    permiso: str
    campos: dict[str, Campo] = field(default_factory=dict)


def _f(
    codigo: str,
    etiqueta: str,
    sql: str,
    tipo: TipoCampo,
    *,
    sensibilidad: Sensibilidad = Sensibilidad.PUBLICO,
    permiso: str | None = None,
    agrupable: bool = True,
    agregable: bool = False,
    valores: tuple[str, ...] = (),
) -> Campo:
    return Campo(
        codigo=codigo,
        etiqueta=etiqueta,
        sql=sql,
        tipo=tipo,
        sensibilidad=sensibilidad,
        permiso=permiso,
        agrupable=agrupable,
        agregable=agregable,
        valores=valores,
    )


CATALOGO: dict[str, Fuente] = {
    "vacantes": Fuente(
        codigo="vacantes",
        etiqueta="Vacantes",
        descripcion="Procesos de selección abiertos por la empresa",
        from_sql="vacante v",
        columna_tenant="v.empresa_id",
        permiso="vacantes:ver",
        campos={
            "titulo": _f("titulo", "Título", "v.titulo", TipoCampo.TEXTO),
            "estado": _f(
                "estado",
                "Estado",
                "v.estado",
                TipoCampo.ENUM,
                valores=("BORRADOR", "PUBLICADA", "PAUSADA", "CERRADA", "CANCELADA"),
            ),
            "modalidad": _f(
                "modalidad",
                "Modalidad",
                "v.modalidad",
                TipoCampo.ENUM,
                valores=("PRESENCIAL", "REMOTO", "HIBRIDO"),
            ),
            "ubicacion": _f("ubicacion", "Ubicación", "v.ubicacion", TipoCampo.TEXTO),
            "cantidad_vacantes": _f(
                "cantidad_vacantes",
                "Cantidad de vacantes",
                "v.cantidad_vacantes",
                TipoCampo.NUMERO,
                agregable=True,
            ),
            "fecha_publicacion": _f(
                "fecha_publicacion",
                "Fecha de publicación",
                "v.fecha_publicacion",
                TipoCampo.FECHA,
                agregable=True,
            ),
        },
    ),
    "usuarios": Fuente(
        codigo="usuarios",
        etiqueta="Usuarios",
        descripcion="Cuentas de acceso al sistema dentro de la empresa",
        from_sql="usuario u",
        columna_tenant="u.empresa_id",
        permiso="usuarios:ver",
        campos={
            "nombres": _f("nombres", "Nombres", "u.nombres", TipoCampo.TEXTO),
            "apellidos": _f("apellidos", "Apellidos", "u.apellidos", TipoCampo.TEXTO),
            "email": _f(
                "email",
                "Correo",
                "u.email",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.PERSONAL,
            ),
            "username": _f("username", "Usuario", "u.username", TipoCampo.TEXTO),
            "telefono": _f(
                "telefono",
                "Teléfono",
                "u.telefono",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.PERSONAL,
            ),
            "activo": _f("activo", "Activo", "u.activo", TipoCampo.BOOLEANO),
            "ultimo_acceso": _f(
                "ultimo_acceso", "Último acceso", "u.ultimo_acceso", TipoCampo.FECHA, agregable=True
            ),
        },
    ),
    "postulaciones": Fuente(
        codigo="postulaciones",
        etiqueta="Postulaciones",
        descripcion="Candidatos postulados a cada vacante",
        from_sql=(
            "postulacion po JOIN vacante v ON v.id=po.vacante_id "
            "JOIN postulante p ON p.id=po.postulante_id AND p.empresa_id=v.empresa_id"
        ),
        columna_tenant="v.empresa_id",
        permiso="postulaciones:ver",
        campos={
            "postulante": _f(
                "postulante",
                "Postulante",
                "concat(p.nombres, ' ', p.apellidos)",
                TipoCampo.TEXTO,
            ),
            "email": _f(
                "email",
                "Correo",
                "p.email",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.PERSONAL,
            ),
            "vacante": _f("vacante", "Vacante", "v.titulo", TipoCampo.TEXTO),
            "estado": _f(
                "estado",
                "Estado",
                "po.estado",
                TipoCampo.ENUM,
                valores=("ACTIVA", "RETIRADA", "DESCARTADA", "CONTRATADA"),
            ),
            "puntaje": _f(
                "puntaje",
                "Puntaje",
                "COALESCE(po.puntaje_manual, po.puntaje_ia)",
                TipoCampo.NUMERO,
                agrupable=False,
                agregable=True,
            ),
            "fecha_postulacion": _f(
                "fecha_postulacion",
                "Fecha de postulación",
                "po.fecha_postulacion",
                TipoCampo.FECHA,
                agregable=True,
            ),
        },
    ),
}


def fuente(codigo: str) -> Fuente | None:
    return CATALOGO.get(codigo)


def campo_de(fuente_codigo: str, campo_codigo: str) -> Campo | None:
    item = CATALOGO.get(fuente_codigo)
    return item.campos.get(campo_codigo) if item else None