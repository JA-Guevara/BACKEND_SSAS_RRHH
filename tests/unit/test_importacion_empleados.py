import csv
from datetime import date
from io import BytesIO, StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from openpyxl import Workbook

from ssas.importacion.application.catalogos import CATALOGS, ImportErrorDetail, parse_file
from ssas.importacion.application.empleados import apply_employees, preview_employees
from ssas.importacion.infrastructure.http.router import authorize_sensitive


def employee_file(**changes):
    columns = CATALOGS["empleados"][1]
    row = dict.fromkeys(columns, "")
    row.update(codigo="E-01", nombres="Ana", apellido_paterno="Paz", ci="001234",
               ci_expedido="SC", fecha_ingreso="2020-01-10", banco="Banco X",
               numero_cuenta="000777", telefono="70000000", email_personal="ana@example.com")
    row.update(changes)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue().encode()


class Session:
    def __init__(self, existing=()):
        self.existing = existing
        self.added = []
        self.flush = AsyncMock()

    async def scalars(self, statement):
        assert statement.compile().params.get("empresa_id_1") == "company-a"
        return SimpleNamespace(all=lambda: self.existing)

    def add(self, item):
        self.added.append(item)


@pytest.mark.asyncio
async def test_employee_preview_hides_private_fields_and_imports_only_selected_company():
    session = Session()
    content = employee_file()
    result = await preview_employees(session, "company-a", content, "empleados.csv")
    assert result["crear"] == 1
    assert "001234" not in str(result)
    assert "000777" not in str(result)
    assert "70000000" not in str(result)
    applied = await apply_employees(session, "company-a", content, "empleados.csv", result["sha256"])
    assert applied["crear"] == 1
    assert session.added[0].empresa_id == "company-a"
    assert session.added[0].usuario_id is None
    assert session.added[0].ci == "001234"
    assert session.added[0].numero_cuenta == "000777"
    assert session.added[0].fecha_ingreso == date(2020, 1, 10)


@pytest.mark.asyncio
async def test_employee_rejects_existing_identity_invalid_dates_and_changed_file():
    session = Session([SimpleNamespace(codigo="e-01", ci="other")])
    content = employee_file()
    result = await preview_employees(session, "company-a", content, "empleados.csv")
    assert result["errores"] == 1
    assert not session.added
    invalid = await preview_employees(Session(), "company-a", employee_file(fecha_salida="2019-01-01"), "empleados.csv")
    assert invalid["errores"] == 1
    with pytest.raises(ImportErrorDetail, match="cambió"):
        await apply_employees(Session(), "company-a", content, "empleados.csv", "0" * 64)


@pytest.mark.asyncio
async def test_employee_import_requires_extra_permission(monkeypatch):
    repository = SimpleNamespace(get_user_permission_codes=AsyncMock(return_value={"importacion:gestionar"}))
    monkeypatch.setattr(
        "ssas.importacion.infrastructure.http.router.SqlAlchemyAuthorizationRepository",
        lambda _session: repository,
    )
    user = SimpleNamespace(id="admin", empresa_id="company-a", es_plataforma=False)
    with pytest.raises(HTTPException) as error:
        await authorize_sensitive("empleados", user, object())
    assert error.value.status_code == 403
    repository.get_user_permission_codes.return_value.add("empleados:importar")
    await authorize_sensitive("empleados", user, object())


def test_employee_excel_dates_and_text_identifiers():
    workbook = Workbook()
    columns = CATALOGS["empleados"][1]
    workbook.active.append(list(columns))
    row = dict.fromkeys(columns, "")
    row.update(codigo="E-01", nombres="Ana", apellido_paterno="Paz", ci="001234",
               ci_expedido="SC", fecha_ingreso=date(2020, 1, 10))
    workbook.active.append([row[key] for key in columns])
    output = BytesIO()
    workbook.save(output)
    assert parse_file("empleados", output.getvalue(), "empleados.xlsx")[1][0]["fecha_ingreso"] == "2020-01-10"
    workbook.active.cell(2, columns.index("ci") + 1).value = 1234
    output = BytesIO()
    workbook.save(output)
    with pytest.raises(ImportErrorDetail, match="formato Texto"):
        parse_file("empleados", output.getvalue(), "empleados.xlsx")
