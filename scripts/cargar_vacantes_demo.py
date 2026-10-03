"""Carga 10 borradores identificados por empresa activa. Sin --apply solo consulta.

Ejecutar desde el backend con PYTHONPATH=src:
    python scripts/cargar_vacantes_demo.py --apply
"""

import argparse
import asyncio

from sqlalchemy import select, text

from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.application.events.vacante_events import VacanteEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.infrastructure.database.session import AsyncSessionLocal, engine
from ssas.vacantes.application.use_cases.gestionar_vacantes import GestionarVacantes
from ssas.vacantes.infrastructure.http.schemas import CrearVacanteRequest, VacanteResponse
from ssas.vacantes.infrastructure.persistence.repositories.vacante_repository import (
    SqlAlchemyVacanteRepository,
)


async def cargar(apply: bool) -> None:
    try:
        async with AsyncSessionLocal() as session:
            # Serializa esta carga para que dos ejecuciones no dupliquen registros.
            await session.execute(text("SELECT pg_advisory_xact_lock(2026090801)"))
            empresas = (await session.scalars(select(EmpresaModel).where(
                EmpresaModel.activo.is_(True), EmpresaModel.eliminado_at.is_(None)
            ).order_by(EmpresaModel.id))).all()
            service = GestionarVacantes(SqlAlchemyVacanteRepository(session))
            events = VacanteEvents(RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)))
            for empresa in empresas:
                cargos = (await session.scalars(select(CargoModel).where(
                    CargoModel.empresa_id == empresa.id,
                    CargoModel.departamento_id.is_not(None),
                ).order_by(CargoModel.id))).all()
                responsable = await session.scalar(select(UserModel.id).where(
                    UserModel.empresa_id == empresa.id,
                    UserModel.is_active.is_(True),
                    UserModel.eliminado_at.is_(None),
                ).order_by(UserModel.created_at, UserModel.id).limit(1))
                if not cargos or not responsable:
                    print(f"{empresa.nombre_comercial}: omitida, falta cargo o responsable")
                    continue
                existentes = {v.titulo for v in await service.listar(empresa.id)}
                creadas = 0
                for index in range(10):
                    titulo = f"[DEMO {index + 1:02d}] Vacante de prueba"
                    if titulo in existentes:
                        continue
                    cargo = cargos[index % len(cargos)]
                    if apply:
                        data = CrearVacanteRequest(
                            cargo_id=cargo.id,
                            departamento_id=cargo.departamento_id,
                            titulo=titulo,
                            descripcion=f"Datos de demostración para el cargo {cargo.nombre}. "
                            "Borrador de prueba; revisar antes de publicar.",
                            modalidad=("PRESENCIAL", "HIBRIDO", "REMOTO")[index % 3],
                            cantidad_vacantes=1,
                        )
                        vacante = await service.crear(
                            empresa.id, responsable, data.model_dump()
                        )
                        VacanteResponse.model_validate(vacante, from_attributes=True)
                        await events.created(
                            empresa_id=empresa.id,
                            actor_label="Carga de vacantes de demostración",
                            record_id=vacante.id,
                            new_data={"titulo": titulo, "estado": vacante.estado},
                        )
                    creadas += 1
                print(f"{empresa.nombre_comercial}: {creadas} "
                      f"{'creadas' if apply else 'pendientes'}; "
                      f"{10 - creadas} demos existentes")
            if apply:
                await session.commit()
                print("Carga confirmada; vacantes en BORRADOR.")
            else:
                await session.rollback()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    asyncio.run(cargar(parser.parse_args().apply))
