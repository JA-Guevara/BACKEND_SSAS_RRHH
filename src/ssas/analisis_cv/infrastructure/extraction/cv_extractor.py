import asyncio
import json
import subprocess
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from ssas.analisis_cv.domain.analysis import AnalisisCvError
from ssas.config.settings import Settings
from ssas.postulaciones.infrastructure.storage.local_cv_storage import LocalCvStorage


def extract_file(path: Path, max_bytes: int, max_chars: int) -> str:
    if path.stat().st_size > max_bytes:
        raise AnalisisCvError("El CV excede el tamano permitido")
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path, strict=True)
        if reader.is_encrypted:
            raise AnalisisCvError("El PDF esta protegido con contrasena")
        if len(reader.pages) > 200:
            raise AnalisisCvError("El PDF excede el limite de paginas")
        parts = []
        length = 0
        for page in reader.pages:
            part = page.extract_text() or ""
            length += len(part) + 1
            if length > max_chars:
                raise AnalisisCvError("El texto del CV excede el limite permitido")
            parts.append(part)
        text = "\n".join(parts)
    elif path.suffix.lower() == ".docx":
        from docx import Document

        try:
            with ZipFile(path) as archive:
                if sum(item.file_size for item in archive.infolist()) > max_bytes * 4:
                    raise AnalisisCvError("El DOCX expandido excede el limite permitido")
        except BadZipFile as exc:
            raise AnalisisCvError("El DOCX no es valido") from exc
        document = Document(path)
        text = "\n".join(
            node.text or "" for node in document.element.body.iter() if node.tag.endswith("}t")
        )
    else:
        raise AnalisisCvError("Solo se admiten CV PDF o DOCX")
    text = text.strip()
    if not text:
        raise AnalisisCvError("El CV no contiene texto extraible; PDF escaneado requiere OCR")
    if len(text) > max_chars:
        raise AnalisisCvError("El texto del CV excede el limite permitido")
    return text


class LocalCvExtractor:
    def __init__(self, config: Settings):
        self.config = config
        self.storage = LocalCvStorage(config.cv_storage_directory)

    async def extract(self, cv_url: str) -> str:
        path = self.storage.resolve_cv(cv_url)
        if path is None:
            raise AnalisisCvError("El archivo CV no existe en el almacenamiento", 404)
        if path.stat().st_size > self.config.ia_max_cv_bytes:
            raise AnalisisCvError("El CV excede el tamano permitido")
        # A killable process bounds parser runtime even for malformed documents.
        try:
            process = await asyncio.to_thread(
                subprocess.run,
                [
                    sys.executable,
                    "-m",
                    "ssas.analisis_cv.infrastructure.extraction.worker",
                    str(path),
                    str(self.config.ia_max_cv_bytes),
                    str(self.config.ia_max_cv_text_chars),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=self.config.ia_extraction_timeout_seconds,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except subprocess.TimeoutExpired as exc:
            raise AnalisisCvError("La extraccion del CV excedio el tiempo permitido", 504) from exc
        except OSError as exc:
            raise AnalisisCvError("No se pudo iniciar la extraccion del CV", 503) from exc

        try:
            result = json.loads(process.stdout)
        except (ValueError, UnicodeError) as exc:
            raise AnalisisCvError("No se pudo extraer el CV") from exc
        if process.returncode:
            raise AnalisisCvError(result.get("error", "No se pudo extraer el CV"))
        return result["text"]
