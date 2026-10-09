from dataclasses import dataclass
from typing import Any, Optional, Type
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Herramienta:
    codigo: str
    descripcion: str          # Lo que lee el modelo o evaluador para decidir si aplica
    permiso: Optional[str]    # Permiso exigido (None para consultas públicas o de usuario base)
    escribe: bool             # True => exige confirmación del usuario antes de ejecutar
    esquema: type[BaseModel]  # Pydantic valida los argumentos
    endpoint: str             # A qué ruta interna se traduce


# Esquemas de argumentos para herramientas de lectura
class ContarPostulacionesArgs(BaseModel):
    vacante_id: Optional[str] = Field(None, description="Identificador de la vacante para filtrar")
    estado: Optional[str] = Field(None, description="Estado de la postulación, ej. PENDIENTE, EN_REVISION")


class BuscarCandidatoArgs(BaseModel):
    query: str = Field(..., description="Nombre, apellido o correo del candidato")
    vacante_id: Optional[str] = Field(None, description="Vacante en la que postula")


class VerAgendaArgs(BaseModel):
    fecha_inicio: Optional[str] = Field(None, description="Fecha de inicio (YYYY-MM-DD)")
    fecha_fin: Optional[str] = Field(None, description="Fecha de fin (YYYY-MM-DD)")


class EstadoVacanteArgs(BaseModel):
    vacante_id: Optional[str] = Field(None, description="ID de vacante opcional")


class ExplicarPantallaArgs(BaseModel):
    concepto: str = Field(..., description="Concepto o duda sobre el sistema o la pantalla")
    pantalla: Optional[str] = Field(None, description="Nombre de la pantalla actual")


# Esquemas de argumentos para herramientas de escritura (SIEMPRE con confirmación)
class ProgramarEntrevistaArgs(BaseModel):
    postulacion_id: str = Field(..., description="Identificador único de la postulación")
    fecha_hora: str = Field(..., description="Fecha y hora de la entrevista (ISO 8601)")
    modalidad: str = Field(default="VIRTUAL", description="PRESENCIAL o VIRTUAL")
    enlace: Optional[str] = Field(None, description="Enlace para reunión virtual si aplica")
    entrevistador_id: Optional[str] = Field(None, description="ID del entrevistador")
    notas: Optional[str] = Field(None, description="Notas o instrucciones adicionales")


class MoverEtapaArgs(BaseModel):
    postulacion_id: str = Field(..., description="Identificador único de la postulación")
    etapa_destino: str = Field(..., description="Nueva etapa (ej. EVALUACION, ENTREVISTA, OFERTA, RECHAZADO)")
    motivo: Optional[str] = Field(None, description="Motivo del cambio de etapa")


class AnalizarCVArgs(BaseModel):
    postulacion_id: str = Field(..., description="Identificador de la postulación para analizar su CV")
    forzar_reanalisis: bool = Field(default=False, description="Forzar nuevo análisis")


class MarcarBancoTalentoArgs(BaseModel):
    candidato_id: str = Field(..., description="Identificador del candidato o postulante")
    etiquetas: Optional[list[str]] = Field(default=None, description="Etiquetas de talento o especialidad")


class GenerarReporteArgs(BaseModel):
    tipo_reporte: str = Field(..., description="Tipo de reporte (ej. postulaciones, empleados, contrataciones)")
    formato: str = Field(default="csv", description="Formato de exportación: csv o pdf")


# Catálogo oficial de herramientas del Asistente
CATALOGO_HERRAMIENTAS: dict[str, Herramienta] = {
    # Herramientas de lectura (inmediatas)
    "contar_postulaciones": Herramienta(
        codigo="contar_postulaciones",
        descripcion="Cuenta la cantidad de postulaciones activas, opcionalmente por vacante o estado.",
        permiso="postulaciones:ver",
        escribe=False,
        esquema=ContarPostulacionesArgs,
        endpoint="/api/v1/postulaciones",
    ),
    "buscar_candidato": Herramienta(
        codigo="buscar_candidato",
        descripcion="Busca un candidato por nombre, apellido o correo y muestra su estado de postulación.",
        permiso="postulaciones:ver",
        escribe=False,
        esquema=BuscarCandidatoArgs,
        endpoint="/api/v1/postulaciones",
    ),
    "ver_agenda": Herramienta(
        codigo="ver_agenda",
        descripcion="Consulta las entrevistas programadas para la semana o rango de fechas.",
        permiso="entrevistas:ver",
        escribe=False,
        esquema=VerAgendaArgs,
        endpoint="/api/v1/entrevistas",
    ),
    "estado_vacante": Herramienta(
        codigo="estado_vacante",
        descripcion="Consulta cuántas vacantes publicadas, activas o en borrador existen en la empresa.",
        permiso="vacantes:ver",
        escribe=False,
        esquema=EstadoVacanteArgs,
        endpoint="/api/v1/vacantes",
    ),
    "explicar_pantalla": Herramienta(
        codigo="explicar_pantalla",
        descripcion="Explica un concepto del sistema de RRHH o la pantalla actual utilizando la base de conocimiento.",
        permiso=None,
        escribe=False,
        esquema=ExplicarPantallaArgs,
        endpoint="/api/v1/chatbot/mensajes",
    ),
    # Herramientas de escritura (requieren confirmación explícita)
    "programar_entrevista": Herramienta(
        codigo="programar_entrevista",
        descripcion="Programa una entrevista para un candidato postulante en una fecha y hora específicas.",
        permiso="entrevistas:gestionar",
        escribe=True,
        esquema=ProgramarEntrevistaArgs,
        endpoint="/api/v1/entrevistas",
    ),
    "mover_etapa": Herramienta(
        codigo="mover_etapa",
        descripcion="Mueve una postulación a una nueva etapa del embudo de selección (ej. EVALUACION, ENTREVISTA).",
        permiso="postulaciones:gestionar",
        escribe=True,
        esquema=MoverEtapaArgs,
        endpoint="/api/v1/postulaciones/{id}/etapa",
    ),
    "analizar_cv": Herramienta(
        codigo="analizar_cv",
        descripcion="Inicia el análisis con inteligencia artificial del currículum vitae de un candidato.",
        permiso="postulaciones:analizar_cv",
        escribe=True,
        esquema=AnalizarCVArgs,
        endpoint="/api/v1/postulaciones/{id}/analizar-cv",
    ),
    "marcar_banco_talento": Herramienta(
        codigo="marcar_banco_talento",
        descripcion="Guarda o etiqueta a un candidato en el banco de talento de la empresa para futuras vacantes.",
        permiso="postulantes:gestionar",
        escribe=True,
        esquema=MarcarBancoTalentoArgs,
        endpoint="/api/v1/postulantes/{id}/banco",
    ),
    "generar_reporte": Herramienta(
        codigo="generar_reporte",
        descripcion="Genera y exporta un reporte estructurado de postulaciones, contrataciones o empleados.",
        permiso="reportes:ejecutar",
        escribe=True,
        esquema=GenerarReporteArgs,
        endpoint="/api/v1/reportes/ejecutar",
    ),
}


def obtener_herramienta(codigo: str) -> Optional[Herramienta]:
    return CATALOGO_HERRAMIENTAS.get(codigo)


def listar_herramientas_para_usuario(
    permisos_usuario: set[str], es_superadmin: bool = False
) -> list[Herramienta]:
    if es_superadmin:
        # Superadministrador solo tiene lectura y ayuda
        return [h for h in CATALOGO_HERRAMIENTAS.values() if not h.escribe]

    disponibles = []
    for h in CATALOGO_HERRAMIENTAS.values():
        if h.permiso is None or h.permiso in permisos_usuario:
            disponibles.append(h)
    return disponibles
