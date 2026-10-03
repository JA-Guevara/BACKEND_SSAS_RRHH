import re
from pathlib import Path

from ssas.postulaciones.domain.entities.postulacion_publica import CvAdjunto
from ssas.postulaciones.ports.outgoing.cv_storage import CvStorage

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
CONTENT_TYPE_POR_DEFECTO = "application/octet-stream"


class LocalCvStorage(CvStorage):
    def __init__(self, base_dir: str | Path = "uploads/cv") -> None:
        self.base_dir = Path(base_dir)

    async def save_cv(self, cv: CvAdjunto, codigo_seguimiento: str) -> str:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        extension = Path(cv.filename).suffix.lower()
        safe_code = re.sub(r"[^A-Z0-9-]", "_", codigo_seguimiento.upper())
        target = self.base_dir / f"{safe_code}{extension}"
        target.write_bytes(cv.content)
        return target.as_posix()

    def resolve_cv(self, cv_url: str) -> Path | None:
        """Traduce el ``cv_url`` almacenado a un archivo real dentro del directorio base.

        Nunca concatena el valor guardado: toma solo el nombre de archivo y comprueba
        que la ruta resuelta siga dentro de ``base_dir``. Así un ``cv_url`` manipulado
        (``../../.env``, rutas absolutas, enlaces simbólicos) no puede sacar la descarga
        del almacén. Devuelve ``None`` si la ruta escapa o el archivo no existe.
        """
        if not cv_url or not cv_url.strip():
            return None
        try:
            base = self.base_dir.resolve()
            candidato = (base / Path(cv_url.strip()).name).resolve()
        except (OSError, ValueError):
            return None
        if not candidato.is_relative_to(base) or not candidato.is_file():
            return None
        return candidato

    @staticmethod
    def content_type(archivo: Path) -> str:
        """Tipo MIME segun la extension aceptada al subir el CV."""
        return CONTENT_TYPES.get(archivo.suffix.lower(), CONTENT_TYPE_POR_DEFECTO)
