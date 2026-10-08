from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.core.api.guards import permiso
from ssas.core.security.dependencies import CurrentUser
from ssas.empleados.infrastructure.http.schemas import (
    EmpleadoDetalle,
    EmpleadoListItem,
    EmpleadosPage,
)
from ssas.empleados.infrastructure.persistence.models.empleado import EmpleadoModel
from ssas.infrastructure.database.session import get_session
from ssas.postulaciones.infrastructure.http.tablero_router import _empresa
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel

router = APIRouter(prefix="/empleados", tags=["Empleados"])


def _cargo_subquery():
    return (
        select(
            PostulacionModel.empleado_id,
            PostulacionModel.id.label("postulacion_id"),
            CargoModel.id.label("cargo_id"),
            CargoModel.nombre.label("cargo_nombre"),
        )
        .join(VacanteModel, PostulacionModel.vacante_id == VacanteModel.id)
        .join(CargoModel, VacanteModel.cargo_id == CargoModel.id)
        .subquery()
    )


@router.get("", response_model=EmpleadosPage, summary="Listar empleados", description="Lista los empleados de la empresa con filtros por nombre, código, estado y cargo.")
async def listar_empleados(
    empresa_id: UUID | None = None,
    q: str | None = None,
    estado: str | None = None,
    cargo_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(permiso("empleados:ver")),
    session: AsyncSession = Depends(get_session),
) -> EmpleadosPage:
    target_empresa_id = _empresa(user, str(empresa_id) if empresa_id else None)
    cargo_sub = _cargo_subquery()

    query = (
        select(EmpleadoModel, cargo_sub.c.cargo_nombre)
        .outerjoin(cargo_sub, EmpleadoModel.id == cargo_sub.c.empleado_id)
        .where(EmpleadoModel.empresa_id == target_empresa_id)
    )

    if q and q.strip():
        term = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        patron = f"%{term}%"
        query = query.where(
            or_(
                EmpleadoModel.nombres.ilike(patron),
                EmpleadoModel.apellido_paterno.ilike(patron),
                EmpleadoModel.codigo.ilike(patron),
            )
        )

    if estado and estado.strip():
        query = query.where(EmpleadoModel.estado == estado.strip().upper())

    if cargo_id:
        query = query.where(cargo_sub.c.cargo_id == str(cargo_id))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.scalar(count_query)) or 0

    results = (
        await session.execute(
            query.order_by(EmpleadoModel.fecha_ingreso.desc(), EmpleadoModel.codigo.asc())
            .offset(offset)
            .limit(limit)
        )
    ).all()

    items = [
        EmpleadoListItem(
            id=emp.id,
            codigo=emp.codigo,
            nombres=emp.nombres,
            apellido_paterno=emp.apellido_paterno,
            apellido_materno=emp.apellido_materno,
            cargo_nombre=cargo_nom,
            fecha_ingreso=emp.fecha_ingreso,
            estado=emp.estado,
        )
        for emp, cargo_nom in results
    ]

    return EmpleadosPage(items=items, total=total)


@router.get("/{id}", response_model=EmpleadoDetalle, summary="Obtener empleado", description="Obtiene la ficha detallada de un empleado, incluyendo datos laborales, personales y bancarios.")
async def obtener_empleado(
    id: UUID,
    empresa_id: UUID | None = None,
    user: CurrentUser = Depends(permiso("empleados:ver")),
    session: AsyncSession = Depends(get_session),
) -> EmpleadoDetalle:
    target_empresa_id = _empresa(user, str(empresa_id) if empresa_id else None)
    cargo_sub = _cargo_subquery()

    query = (
        select(EmpleadoModel, cargo_sub.c.cargo_nombre, cargo_sub.c.postulacion_id)
        .outerjoin(cargo_sub, EmpleadoModel.id == cargo_sub.c.empleado_id)
        .where(EmpleadoModel.empresa_id == target_empresa_id, EmpleadoModel.id == str(id))
    )

    row = (await session.execute(query)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    emp, cargo_nom, post_id = row
    return EmpleadoDetalle(
        id=emp.id,
        codigo=emp.codigo,
        nombres=emp.nombres,
        apellido_paterno=emp.apellido_paterno,
        apellido_materno=emp.apellido_materno,
        cargo_nombre=cargo_nom,
        fecha_ingreso=emp.fecha_ingreso,
        estado=emp.estado,
        empresa_id=emp.empresa_id,
        ci=emp.ci,
        ci_expedido=emp.ci_expedido,
        fecha_nacimiento=emp.fecha_nacimiento,
        genero=emp.genero,
        estado_civil=emp.estado_civil,
        direccion=emp.direccion,
        telefono=emp.telefono,
        email_personal=emp.email_personal,
        contacto_emergencia=emp.contacto_emergencia,
        telefono_emergencia=emp.telefono_emergencia,
        nua_cua=emp.nua_cua,
        afp=emp.afp,
        banco=emp.banco,
        numero_cuenta=emp.numero_cuenta,
        tipo_cuenta=emp.tipo_cuenta,
        fecha_salida=emp.fecha_salida,
        motivo_salida=emp.motivo_salida,
        foto_url=emp.foto_url,
        fecha_registro=emp.fecha_registro,
        postulacion_id=post_id,
    )
