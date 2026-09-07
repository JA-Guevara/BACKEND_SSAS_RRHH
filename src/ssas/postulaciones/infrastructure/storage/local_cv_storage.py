from pathlib import Path
import re

from ssas.postulaciones.domain.entities.postulacion_publica import CvAdjunto
from ssas.postulaciones.ports.outgoing.cv_storage import CvStorage


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
