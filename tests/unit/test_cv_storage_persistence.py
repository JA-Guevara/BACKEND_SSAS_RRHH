import pytest

from ssas.config.settings import Settings
from ssas.postulaciones.domain.entities.postulacion_publica import CvAdjunto
from ssas.postulaciones.infrastructure.storage.local_cv_storage import (
    CvStorageUnavailableError,
    LocalCvStorage,
)


def test_railway_volume_becomes_default_cv_and_backup_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))
    monkeypatch.delenv("CV_STORAGE_DIRECTORY", raising=False)
    monkeypatch.delenv("BACKUP_FILES_DIRECTORY", raising=False)
    config = Settings(_env_file=None, app_secret_key="test")
    assert config.cv_storage_directory == str(tmp_path / "cv")
    assert config.backup_files_directory == str(tmp_path / "cv")


@pytest.mark.asyncio
async def test_railway_rejects_ephemeral_cv_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "project-test")
    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    cv = CvAdjunto(filename="cv.pdf", content_type="application/pdf", content=b"test")
    with pytest.raises(CvStorageUnavailableError, match="volumen persistente"):
        await LocalCvStorage(tmp_path).save_cv(cv, "POST-12345678")
    assert not list(tmp_path.iterdir())

    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path / "volume"))
    with pytest.raises(CvStorageUnavailableError, match="volumen persistente"):
        await LocalCvStorage(tmp_path / "outside").save_cv(cv, "POST-12345678")


@pytest.mark.asyncio
async def test_cv_remains_available_to_new_storage_instance(tmp_path, monkeypatch):
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "project-test")
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))
    directory = tmp_path / "cv"
    cv = CvAdjunto(filename="cv.pdf", content_type="application/pdf", content=b"sample PDF")
    cv_url = await LocalCvStorage(directory).save_cv(cv, "POST-12345678")

    path_after_restart = LocalCvStorage(directory).resolve_cv(cv_url)
    assert path_after_restart is not None
    assert path_after_restart.read_bytes() == cv.content
