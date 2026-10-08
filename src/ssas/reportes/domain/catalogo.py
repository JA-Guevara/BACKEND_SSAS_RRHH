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
            "en_banco_talento": _f(
                "en_banco_talento",
                "En banco de talentos",
                "p.en_banco_talento",
                TipoCampo.BOOLEANO,
            ),
        },
    ),
    "entrevistas": Fuente(
        codigo="entrevistas",
        etiqueta="Entrevistas",
        descripcion="Entrevistas agendadas dentro del proceso de selección",
        from_sql=(
            "entrevista en JOIN postulacion po ON po.id=en.postulacion_id "
            "JOIN vacante v ON v.id=po.vacante_id "
            "JOIN postulante p ON p.id=po.postulante_id AND p.empresa_id=v.empresa_id"
        ),
        columna_tenant="v.empresa_id",
        permiso="entrevistas:ver",
        campos={
            "vacante": _f("vacante", "Vacante", "v.titulo", TipoCampo.TEXTO),
            "postulante": _f(
                "postulante", "Postulante", "concat(p.nombres, ' ', p.apellidos)", TipoCampo.TEXTO
            ),
            "tipo": _f(
                "tipo",
                "Tipo",
                "en.tipo",
                TipoCampo.ENUM,
                valores=("TECNICA", "PSICOTECNICA", "MEDICA", "OTRO"),
            ),
            "modalidad": _f(
                "modalidad",
                "Modalidad",
                "en.modalidad",
                TipoCampo.ENUM,
                valores=("VIRTUAL", "PRESENCIAL", "TELEFONICA"),
            ),
            "estado": _f(
                "estado",
                "Estado",
                "en.estado",
                TipoCampo.ENUM,
                valores=("PROGRAMADA", "CONFIRMADA", "REALIZADA", "CANCELADA"),
            ),
            "fecha_hora": _f(
                "fecha_hora", "Fecha y hora", "en.fecha_hora", TipoCampo.FECHA, agregable=True
            ),
            "duracion_min": _f(
                "duracion_min",
                "Duración (min)",
                "en.duracion_min",
                TipoCampo.NUMERO,
                agregable=True,
            ),
            "puntaje": _f(
                "puntaje",
                "Puntaje",
                "en.puntaje",
                TipoCampo.NUMERO,
                sensibilidad=Sensibilidad.INTERNO,
                agregable=True,
            ),
            "recomendacion": _f(
                "recomendacion", "Recomendación", "en.recomendacion", TipoCampo.TEXTO
            ),
            "observaciones": _f(
                "observaciones",
                "Observaciones",
                "en.observaciones",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.INTERNO,
            ),
        },
    ),
    "evaluaciones": Fuente(
        codigo="evaluaciones",
        etiqueta="Evaluaciones",
        descripcion="Evaluaciones técnicas y psicotécnicas por postulación",
        from_sql=(
            "evaluacion ev JOIN postulacion po ON po.id=ev.postulacion_id "
            "JOIN vacante v ON v.id=po.vacante_id"
        ),
        columna_tenant="v.empresa_id",
        permiso="evaluaciones:ver",
        campos={
            "vacante": _f("vacante", "Vacante", "v.titulo", TipoCampo.TEXTO),
            "tipo": _f(
                "tipo",
                "Tipo",
                "ev.tipo",
                TipoCampo.ENUM,
                valores=("TECNICA", "PSICOTECNICA", "MEDICA", "OTRO"),
            ),
            "nombre": _f("nombre", "Nombre", "ev.nombre", TipoCampo.TEXTO),
            "puntaje": _f("puntaje", "Puntaje", "ev.puntaje", TipoCampo.NUMERO, agregable=True),
            "puntaje_maximo": _f(
                "puntaje_maximo", "Puntaje máximo", "ev.puntaje_maximo", TipoCampo.NUMERO
            ),
            "aprobado": _f("aprobado", "Aprobado", "ev.aprobado", TipoCampo.BOOLEANO),
            "observaciones": _f(
                "observaciones",
                "Observaciones",
                "ev.observaciones",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.INTERNO,
            ),
            "fecha": _f("fecha", "Fecha", "ev.fecha", TipoCampo.FECHA, agregable=True),
        },
    ),
    "analisis_cv": Fuente(
        codigo="analisis_cv",
        etiqueta="Análisis de CV",
        descripcion="Resultados del análisis de afinidad de currículums",
        from_sql=(
            "analisis_cv ac JOIN postulacion po ON po.id=ac.postulacion_id "
            "JOIN vacante v ON v.id=po.vacante_id"
        ),
        columna_tenant="v.empresa_id",
        permiso="postulaciones:ver",
        campos={
            "vacante": _f("vacante", "Vacante", "v.titulo", TipoCampo.TEXTO),
            "puntaje_afinidad": _f(
                "puntaje_afinidad",
                "Puntaje de afinidad",
                "ac.puntaje_afinidad",
                TipoCampo.NUMERO,
                agregable=True,
            ),
            "anios_experiencia_detectados": _f(
                "anios_experiencia_detectados",
                "Años detectados",
                "ac.anios_experiencia_detectados",
                TipoCampo.NUMERO,
                agregable=True,
            ),
            "modelo_usado": _f("modelo_usado", "Modelo usado", "ac.modelo_usado", TipoCampo.TEXTO),
            "resumen_ia": _f(
                "resumen_ia",
                "Resumen",
                "ac.resumen_ia",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.INTERNO,
            ),
            "tiempo_proceso_ms": _f(
                "tiempo_proceso_ms", "Tiempo de proceso (ms)", "ac.tiempo_proceso_ms", TipoCampo.NUMERO
            ),
            "fecha_analisis": _f(
                "fecha_analisis", "Fecha de análisis", "ac.fecha_analisis", TipoCampo.FECHA, agregable=True
            ),
        },
    ),
    "empleados": Fuente(
        codigo="empleados",
        etiqueta="Empleados",
        descripcion="Nómina de empleados con datos laborales y personales",
        from_sql="empleado e",
        columna_tenant="e.empresa_id",
        permiso="empleados:ver",
        campos={
            "codigo": _f("codigo", "Código", "e.codigo", TipoCampo.TEXTO),
            "nombres": _f("nombres", "Nombres", "e.nombres", TipoCampo.TEXTO),
            "apellido_paterno": _f(
                "apellido_paterno", "Apellido paterno", "e.apellido_paterno", TipoCampo.TEXTO
            ),
            "apellido_materno": _f(
                "apellido_materno", "Apellido materno", "e.apellido_materno", TipoCampo.TEXTO
            ),
            "ci": _f(
                "ci", "CI", "e.ci", TipoCampo.TEXTO, sensibilidad=Sensibilidad.PERSONAL
            ),
            "telefono": _f(
                "telefono", "Teléfono", "e.telefono", TipoCampo.TEXTO, sensibilidad=Sensibilidad.PERSONAL
            ),
            "email_personal": _f(
                "email_personal",
                "Correo personal",
                "e.email_personal",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.PERSONAL,
            ),
            "direccion": _f(
                "direccion", "Dirección", "e.direccion", TipoCampo.TEXTO, sensibilidad=Sensibilidad.PERSONAL
            ),
            "nua_cua": _f(
                "nua_cua", "NUA/CUA", "e.nua_cua", TipoCampo.TEXTO, sensibilidad=Sensibilidad.CONFIDENCIAL
            ),
            "afp": _f("afp", "AFP", "e.afp", TipoCampo.TEXTO),
            "banco": _f("banco", "Banco", "e.banco", TipoCampo.TEXTO),
            "numero_cuenta": _f(
                "numero_cuenta",
                "Número de cuenta",
                "e.numero_cuenta",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.CONFIDENCIAL,
            ),
            "tipo_cuenta": _f("tipo_cuenta", "Tipo de cuenta", "e.tipo_cuenta", TipoCampo.TEXTO),
            "fecha_ingreso": _f(
                "fecha_ingreso", "Fecha de ingreso", "e.fecha_ingreso", TipoCampo.FECHA, agregable=True
            ),
            "fecha_salida": _f("fecha_salida", "Fecha de salida", "e.fecha_salida", TipoCampo.FECHA),
            "estado": _f(
                "estado", "Estado", "e.estado", TipoCampo.ENUM, valores=("ACTIVO", "INACTIVO")
            ),
        },
    ),
    "bitacora": Fuente(
        codigo="bitacora",
        etiqueta="Bitácora",
        descripcion="Eventos auditados de la empresa",
        from_sql="bitacora b",
        columna_tenant="b.empresa_id",
        permiso="bitacora:ver",
        campos={
            "actor": _f("actor", "Actor", "b.actor_etiqueta", TipoCampo.TEXTO),
            "modulo": _f("modulo", "Módulo", "b.modulo", TipoCampo.TEXTO),
            "accion": _f("accion", "Acción", "b.accion", TipoCampo.TEXTO),
            "nivel": _f(
                "nivel",
                "Nivel",
                "b.nivel",
                TipoCampo.ENUM,
                valores=("INFO", "WARNING", "ERROR", "CRITICAL"),
            ),
            "tabla_afectada": _f(
                "tabla_afectada", "Tabla afectada", "b.tabla_afectada", TipoCampo.TEXTO
            ),
            "ip_origen": _f(
                "ip_origen",
                "IP de origen",
                "CAST(b.ip_origen AS TEXT)",
                TipoCampo.TEXTO,
                sensibilidad=Sensibilidad.PERSONAL,
            ),
            "fecha": _f("fecha", "Fecha", "b.fecha", TipoCampo.FECHA, agregable=True),
        },
    ),
}


def fuente(codigo: str) -> Fuente | None:
    return CATALOGO.get(codigo)


def campo_de(fuente_codigo: str, campo_codigo: str) -> Campo | None:
    item = CATALOGO.get(fuente_codigo)
    return item.campos.get(campo_codigo) if item else None