import io

import pytest
from PIL import Image

from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.infrastructure.http.schemas import (
    UsuarioResponse,
)
from ssas.usuarios.infrastructure.storage.avatar_storage import (
    MAX_AVATAR_BYTES,
    delete_avatar_file,
    get_avatar_path,
    process_and_save_avatar,
)


def _crear_imagen_bytes(formato="JPEG", size=(600, 400), color=(100, 150, 200)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=formato)
    return buf.getvalue()


def test_avatar_crop_and_resize(tmp_path, monkeypatch):
    monkeypatch.setattr("ssas.config.settings.settings.cv_storage_directory", str(tmp_path / "cv"))

    raw = _crear_imagen_bytes("PNG", size=(800, 600))
    url = process_and_save_avatar("test-user-123", raw)

    assert url == "/api/v1/usuarios/test-user-123/foto"

    avatar_path = get_avatar_path("test-user-123")
    assert avatar_path is not None
    assert avatar_path.exists()

    # Verificar que el resultado sea 512x512
    with Image.open(avatar_path) as saved_img:
        assert saved_img.size == (512, 512)

    # Eliminar
    delete_avatar_file("test-user-123")
    assert get_avatar_path("test-user-123") is None


def test_avatar_rechaza_archivo_no_imagen():
    with pytest.raises(ValueError, match="no es una imagen válida"):
        process_and_save_avatar("bad-user", b"este no es un archivo de imagen")


def test_avatar_rechaza_archivo_grande():
    fake_large_bytes = b"0" * (MAX_AVATAR_BYTES + 10)
    with pytest.raises(ValueError, match="supera el tamaño máximo"):
        process_and_save_avatar("oversized-user", fake_large_bytes)


def test_usuario_response_incluye_foto_url():
    user = Usuario(
        id="usr-1",
        empresa_id=None,
        nombre="Test",
        apellido="User",
        email="test@example.com",
        username="testuser",
        foto_url="/api/v1/usuarios/usr-1/foto",
    )
    schema = UsuarioResponse(
        id=user.id,
        empresa_id=user.empresa_id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        email_verified=user.email_verified,
        must_change_password=user.must_change_password,
        failed_login_attempts=user.failed_login_attempts,
        foto_url=user.foto_url,
    )
    assert schema.foto_url == "/api/v1/usuarios/usr-1/foto"
