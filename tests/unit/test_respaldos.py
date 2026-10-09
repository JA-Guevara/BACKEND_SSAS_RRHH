from pathlib import Path

import pytest

from ssas.respaldos.infrastructure.services import postgres_tools
from ssas.respaldos.infrastructure.services.storage import (
    BackupStorageError,
    SupabaseBackupStorage,
)


def test_database_password_is_passed_through_environment() -> None:
    args, environment = postgres_tools._connection(
        "postgresql+psycopg://postgres.usuario:clave%24segura@db.example.com:5432/postgres"
    )

    assert "clave$segura" not in " ".join(args)
    assert environment["PGPASSWORD"] == "clave$segura"
    assert environment["PGSSLMODE"] == "require"
    assert args == [
        "--host", "db.example.com", "--port", "5432",
        "--username", "postgres.usuario", "--dbname", "postgres",
    ]


def test_create_dump_uses_private_custom_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict = {}
    monkeypatch.setattr(postgres_tools.shutil, "which", lambda _: "/usr/bin/pg_dump")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(postgres_tools.subprocess, "run", fake_run)
    destination = tmp_path / "backup.dump"
    postgres_tools.create_dump(
        "postgresql://usuario:clave@localhost:5432/rrhh", destination, "pg_dump"
    )

    command = captured["command"]
    assert "--format=custom" in command
    assert "--schema=public" in command
    assert str(destination) in command
    assert "clave" not in " ".join(command)


def test_storage_requires_server_credentials() -> None:
    with pytest.raises(BackupStorageError, match="SUPABASE_URL"):
        SupabaseBackupStorage(None, None, "respaldos")


def test_calcular_proxima_ejecucion_diaria() -> None:
    from datetime import UTC, datetime

    from ssas.respaldos.infrastructure.services.jobs import calcular_proxima_ejecucion

    base = datetime(2026, 10, 8, 10, 0, tzinfo=UTC)
    proxima = calcular_proxima_ejecucion("DIARIA", "14:00", base_time=base)
    assert proxima == datetime(2026, 10, 8, 14, 0, tzinfo=UTC)

    proxima_manana = calcular_proxima_ejecucion("DIARIA", "08:00", base_time=base)
    assert proxima_manana == datetime(2026, 10, 9, 8, 0, tzinfo=UTC)


def test_calcular_proxima_ejecucion_semanal() -> None:
    from datetime import UTC, datetime

    from ssas.respaldos.infrastructure.services.jobs import calcular_proxima_ejecucion

    # 2026-10-08 es Jueves (weekday = 3)
    base = datetime(2026, 10, 8, 10, 0, tzinfo=UTC)
    # Lunes siguiente (weekday = 0): 2026-10-12
    proxima = calcular_proxima_ejecucion("SEMANAL", "03:00", dia_semana=0, base_time=base)
    assert proxima == datetime(2026, 10, 12, 3, 0, tzinfo=UTC)
