import io
import logging
from pathlib import Path

from PIL import Image

from ssas.config.settings import settings

logger = logging.getLogger(__name__)

MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB
PERMITTED_FORMATS = {"jpeg", "jpg", "png", "webp"}


def get_fotos_dir() -> Path:
    cv_dir = Path(settings.cv_storage_directory)
    fotos_dir = cv_dir.parent / "fotos"
    fotos_dir.mkdir(parents=True, exist_ok=True)
    return fotos_dir


def get_avatar_path(user_id: str) -> Path | None:
    target = get_fotos_dir() / f"avatar_{user_id}.jpg"
    return target if target.is_file() else None


def delete_avatar_file(user_id: str) -> None:
    target = get_fotos_dir() / f"avatar_{user_id}.jpg"
    if target.is_file():
        try:
            target.unlink()
        except OSError:
            logger.warning("No se pudo eliminar el archivo de avatar %s", target)


def process_and_save_avatar(user_id: str, content: bytes) -> str:
    """Valida el contenido de imagen con Pillow, recorta a 512x512 y guarda en el volumen."""
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido de 2 MB.")

    try:
        # 1. Validar cabecera real
        probe = Image.open(io.BytesIO(content))
        probe.verify()

        # 2. Reabrir para procesamiento (verify invalida el descriptor)
        image = Image.open(io.BytesIO(content))
        fmt = (image.format or "").lower()
        if fmt not in PERMITTED_FORMATS:
            raise ValueError("Formato de imagen no soportado. Usa JPEG, PNG o WebP.")

        # 3. Recorte centrado a proporción 1:1
        width, height = image.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        image = image.crop((left, top, left + min_dim, top + min_dim))

        # 4. Redimensionar a 512x512 de alta calidad
        image = image.resize((512, 512), Image.Resampling.LANCZOS)

        # 5. Convertir a RGB (maneja RGBA, P, etc.) y optimizar JPEG
        rgb_image = image.convert("RGB")
        target_path = get_fotos_dir() / f"avatar_{user_id}.jpg"

        output_buffer = io.BytesIO()
        rgb_image.save(output_buffer, format="JPEG", quality=88, optimize=True)
        target_path.write_bytes(output_buffer.getvalue())

        return f"/api/v1/usuarios/{user_id}/foto"
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("El archivo subido no es una imagen válida o está dañado.") from exc
