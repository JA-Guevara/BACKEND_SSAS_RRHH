import io
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from ssas.config.settings import settings

logger = logging.getLogger(__name__)

MAX_LOGO_BYTES = 1 * 1024 * 1024  # 1 MB
PERMITTED_RASTER_FORMATS = {"jpeg", "jpg", "png", "webp"}


def get_logos_dir() -> Path:
    cv_dir = Path(settings.cv_storage_directory)
    logos_dir = cv_dir.parent / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    return logos_dir


def get_logo_path(empresa_id: str) -> tuple[Path, str] | None:
    directory = get_logos_dir()
    for ext, mime in [("png", "image/png"), ("svg", "image/svg+xml"), ("jpg", "image/jpeg"), ("webp", "image/webp")]:
        candidate = directory / f"logo_{empresa_id}.{ext}"
        if candidate.is_file():
            return candidate, mime
    return None


def delete_logo_file(empresa_id: str) -> None:
    directory = get_logos_dir()
    for ext in ["png", "svg", "jpg", "webp"]:
        candidate = directory / f"logo_{empresa_id}.{ext}"
        if candidate.is_file():
            try:
                candidate.unlink()
            except OSError:
                logger.warning("No se pudo eliminar el archivo de logo %s", candidate)


def _is_svg(content: bytes) -> bool:
    prefix = content[:200].decode("utf-8", errors="ignore").strip().lower()
    return "<svg" in prefix or ("<?xml" in prefix and "<svg" in content[:1000].decode("utf-8", errors="ignore").lower())


def _sanitize_svg(content: bytes) -> bytes:
    try:
        root = ET.fromstring(content)
    except Exception as exc:
        raise ValueError("El archivo SVG no tiene una estructura XML válida.") from exc

    # Tag local de la raíz debe ser svg
    tag_name = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag_name.lower() != "svg":
        raise ValueError("El archivo no es un documento SVG válido.")

    # Remover scripts y tags ejecutables
    dangerous_tags = {"script", "iframe", "object", "embed", "foreignobject"}
    elements_to_remove = []
    for parent in root.iter():
        for child in list(parent):
            child_tag = child.tag.split("}")[-1].lower() if "}" in child.tag else child.tag.lower()
            if child_tag in dangerous_tags:
                elements_to_remove.append((parent, child))
            else:
                # Limpiar atributos de eventos onload, onclick, etc.
                attribs_to_del = [
                    k for k in child.attrib
                    if k.lower().startswith("on") or (
                        k.lower().endswith("href") and child.attrib[k].strip().lower().startswith("javascript:")
                    )
                ]
                for k in attribs_to_del:
                    del child.attrib[k]

    for parent, child in elements_to_remove:
        parent.remove(child)

    # Limpiar atributos de la raíz también
    attribs_to_del = [
        k for k in root.attrib
        if k.lower().startswith("on") or (
            k.lower().endswith("href") and root.attrib[k].strip().lower().startswith("javascript:")
        )
    ]
    for k in attribs_to_del:
        del root.attrib[k]

    return ET.tostring(root, encoding="utf-8")


def process_and_save_logo(empresa_id: str, content: bytes) -> str:
    """Valida, sanea/redimensiona y guarda el logotipo en el almacenamiento persistente."""
    if len(content) > MAX_LOGO_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido de 1 MB.")

    delete_logo_file(empresa_id)

    if _is_svg(content):
        sanitized = _sanitize_svg(content)
        target = get_logos_dir() / f"logo_{empresa_id}.svg"
        target.write_bytes(sanitized)
        return f"/api/v1/empresas/{empresa_id}/logo"

    try:
        probe = Image.open(io.BytesIO(content))
        probe.verify()

        image = Image.open(io.BytesIO(content))
        fmt = (image.format or "").lower()
        if fmt not in PERMITTED_RASTER_FORMATS:
            raise ValueError("Formato no soportado. Usa PNG, JPG, WebP o SVG.")

        # Redimensionar conservando proporción a un máximo de 512x512
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)

        # Si tiene transparencia o paleta, guardar como PNG para preservarla
        target = get_logos_dir() / f"logo_{empresa_id}.png"
        output_buffer = io.BytesIO()

        if image.mode in ("RGBA", "LA", "P"):
            image.save(output_buffer, format="PNG", optimize=True)
        else:
            image.convert("RGB").save(output_buffer, format="PNG", optimize=True)

        target.write_bytes(output_buffer.getvalue())
        return f"/api/v1/empresas/{empresa_id}/logo"
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("El archivo subido no es una imagen válida o está dañado.") from exc
