"""Company-scoped import of historical employee records."""

from datetime import date
from uuid import uuid4

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from ssas.empleados.infrastructure.persistence.models.empleado import EmpleadoModel
from ssas.importacion.application.catalogos import ImportErrorDetail, parse_file

EMAIL = TypeAdapter(EmailStr)
REQUIRED = ("codigo", "nombres", "apellido_paterno", "ci", "ci_expedido", "fecha_ingreso")
LIMITS = {
    "codigo": 40, "nombres": 120, "apellido_paterno": 120, "apellido_materno": 120,
    "ci": 30, "ci_expedido": 10, "genero": 20, "estado_civil": 30,
    "telefono": 40, "email_personal": 150, "contacto_emergencia": 200,
    "telefono_emergencia": 40, "nua_cua": 40, "afp": 80, "banco": 120,
    "numero_cuenta": 80, "tipo_cuenta": 40, "estado": 20,
}
DATES = ("fecha_ingreso", "fecha_nacimiento", "fecha_salida")


def _dates(row: dict[str, str], issues: list[str]) -> dict[str, date | None]:
    parsed = {}
    for field in DATES:
        try:
            parsed[field] = date.fromisoformat(row[field]) if row[field] else None
        except ValueError:
            issues.append(f"{field}: usa AAAA-MM-DD")
            parsed[field] = None
    if parsed["fecha_ingreso"] and parsed["fecha_salida"] and parsed["fecha_salida"] < parsed["fecha_ingreso"]:
        issues.append("La fecha de salida no puede ser anterior al ingreso")
    return parsed


async def preview_employees(session, company_id: str, content: bytes, filename: str):
    digest, rows = parse_file("empleados", content, filename)
    existing = (await session.scalars(
        select(EmpleadoModel).where(EmpleadoModel.empresa_id == company_id)
    )).all()
    codes = {item.codigo.casefold() for item in existing}
    cis = {item.ci.casefold() for item in existing}
    seen_codes: set[str] = set()
    seen_cis: set[str] = set()
    result = []
    for number, row in enumerate(rows, 2):
        issues = []
        for field in REQUIRED:
            if not row[field]:
                issues.append(f"{field} es obligatorio")
        for field, limit in LIMITS.items():
            if len(row[field]) > limit:
                issues.append(f"{field} excede {limit} caracteres")
        if any(len(row[field]) > 4000 for field in ("direccion", "motivo_salida")):
            issues.append("Un campo de texto excede 4000 caracteres")
        dates = _dates(row, issues)
        state = row["estado"].upper() or "ACTIVO"
        if state not in {"ACTIVO", "INACTIVO"}:
            issues.append("Estado inválido: usa ACTIVO o INACTIVO")
        if dates["fecha_salida"] and state != "INACTIVO":
            issues.append("Un empleado con fecha de salida debe estar INACTIVO")
        if row["email_personal"]:
            try:
                EMAIL.validate_python(row["email_personal"])
            except ValidationError:
                issues.append("Correo personal inválido")
        code, ci = row["codigo"].casefold(), row["ci"].casefold()
        if code in seen_codes or ci in seen_cis:
            issues.append("Código o CI repetido en el archivo")
        if code in codes or ci in cis:
            issues.append("Código o CI ya existe en esta empresa")
        seen_codes.add(code)
        seen_cis.add(ci)
        result.append({
            "fila": number,
            "datos": {key: row[key] for key in ("codigo", "nombres", "apellido_paterno", "estado", "fecha_ingreso")},
            "accion": "error" if issues else "crear",
            "errores": issues,
        })
    return {
        "sha256": digest, "filas": result,
        "crear": sum(item["accion"] == "crear" for item in result),
        "omitir": 0, "errores": sum(item["accion"] == "error" for item in result),
    }


async def apply_employees(session, company_id: str, content: bytes, filename: str, expected_digest: str):
    result = await preview_employees(session, company_id, content, filename)
    if result["sha256"] != expected_digest:
        raise ImportErrorDetail("El archivo cambió desde la vista previa")
    if result["errores"]:
        raise ImportErrorDetail("Corrige las filas marcadas antes de importar")
    _, rows = parse_file("empleados", content, filename)
    for row in rows:
        dates = _dates(row, [])
        values = {key: value or None for key, value in row.items() if key not in (*DATES, "estado")}
        session.add(EmpleadoModel(
            id=str(uuid4()), empresa_id=company_id, usuario_id=None,
            **values, **dates, estado=row["estado"].upper() or "ACTIVO",
        ))
    await session.flush()
    return result
