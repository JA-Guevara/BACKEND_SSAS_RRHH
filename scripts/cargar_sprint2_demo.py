"""Synthetic Sprint2 browser/Postman data, restricted to the disposable local DB."""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4


def configure():
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import ArgumentError

    target = os.environ.get("SPRINT2_TEST_DATABASE_URL", "")
    try:
        url = make_url(target)
        safe = (
            url.drivername == "postgresql+psycopg"
            and url.host in {"localhost", "127.0.0.1"}
            and url.port == 55432
            and url.database == "sprint2"
            and url.username == "sprint2"
            and not url.password
            and not url.query
        )
    except (ArgumentError, TypeError, ValueError):
        safe = False
    if not safe:
        raise SystemExit(
            "Requires SPRINT2_TEST_DATABASE_URL: loopback:55432/sprint2, user sprint2, no password/options"
        )
    os.environ.update(
        SETTINGS_ENV_FILE=str(Path(__file__).with_name(".sprint2-env-does-not-exist")),
        APP_ENV="development",
        APP_SECRET_KEY="test",
        DATABASE_URL=target,
        APP_AUDIT_ENCRYPTION_KEY="11" * 32,
    )
    os.environ.pop("OPENAI_API_KEY", None)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def cargar(args):
    from reportlab.pdfgen import canvas
    from sqlalchemy import select, text

    from ssas.analisis_cv.infrastructure.persistence.models.analisis_cv import AnalisisCvModel
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
    from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
    from ssas.evaluaciones.infrastructure.persistence.models.evaluacion import EvaluacionModel
    from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
    from ssas.infrastructure.database.session import AsyncSessionLocal, engine
    from ssas.platform.application.use_cases.provision_empresa import ProvisionEmpresa
    from ssas.platform.infrastructure.http.schemas import ProvisionEmpresaRequest
    from ssas.postulaciones.domain.entities.postulacion_publica import CvAdjunto
    from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
        EtapaReclutamientoModel,
    )
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
    from ssas.postulaciones.infrastructure.storage.local_cv_storage import LocalCvStorage
    from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
    from ssas.postulantes.infrastructure.persistence.models.postulante_habilidad import (
        PostulanteHabilidadModel,
    )
    from ssas.roles.infrastructure.persistence.repositories.authorization_repository import (
        SqlAlchemyAuthorizationRepository,
    )
    from ssas.suscripciones.application.policy import SubscriptionPolicy
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
    from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import (
        VacanteHabilidadModel,
    )

    created_admin = False
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(text("SELECT pg_advisory_xact_lock(2026092702)"))
            empresa = await s.scalar(
                select(EmpresaModel).where(EmpresaModel.slug == args.empresa_slug)
            )
            if not args.apply:
                print(
                    "Dry run: named company "
                    + ("exists" if empresa else "requires provisioning")
                    + "; no data written."
                )
                return
            if empresa is None:
                if not args.create_empresa:
                    raise ValueError(
                        "Company missing: use --create-empresa with administrator environment variables"
                    )
                password = os.environ.get("SPRINT2_DEMO_ADMIN_PASSWORD", "")
                email = os.environ.get("SPRINT2_DEMO_ADMIN_EMAIL", "")
                username = os.environ.get("SPRINT2_DEMO_ADMIN_USERNAME", "")
                if not all((password, email, username)):
                    raise ValueError(
                        "Set SPRINT2_DEMO_ADMIN_PASSWORD, SPRINT2_DEMO_ADMIN_EMAIL and SPRINT2_DEMO_ADMIN_USERNAME"
                    )
                # ProvisionEmpresa validates the strict password policy and creates roles,
                # stages, subscription and module assignments; no outbound email is sent.
                request = ProvisionEmpresaRequest(
                    empresa={
                        "slug": args.empresa_slug,
                        "razon_social": "Sprint2 synthetic demo",
                        "nombre_comercial": "Sprint2 Demo",
                    },
                    administrador={
                        "nombre": "Demo",
                        "apellido": "Sprint2",
                        "email": email,
                        "username": username,
                        "password": password,
                    },
                )
                empresa, user, _ = await ProvisionEmpresa(s).execute(request)
                created_admin = True
            else:
                if not empresa.activo or empresa.eliminado_at:
                    raise ValueError("Named company is inactive")
                user = None
                for candidate in (
                    await s.scalars(
                        select(UserModel)
                        .where(
                            UserModel.empresa_id == empresa.id,
                            UserModel.is_active.is_(True),
                            UserModel.eliminado_at.is_(None),
                        )
                        .order_by(UserModel.id)
                    )
                ).all():
                    codes = await SqlAlchemyAuthorizationRepository(s).get_user_permission_codes(
                        candidate.id, empresa.id
                    )
                    if {
                        "entrevistas:registrar_resultado",
                        "evaluaciones:gestionar",
                        "postulaciones:contratar",
                    } <= codes:
                        user = candidate
                        break
                if user is None:
                    raise ValueError(
                        "Company requires a provisioned selection administrator with enabled modules"
                    )
            await SubscriptionPolicy(s).require_operational(empresa.id)
            initial = await s.scalar(
                select(EtapaReclutamientoModel).where(
                    EtapaReclutamientoModel.empresa_id == empresa.id,
                    EtapaReclutamientoModel.es_inicial.is_(True),
                )
            )
            if initial is None:
                raise ValueError("Company has no initial recruitment stage")

            async def get_or_create(model, filters, **values):
                item = await s.scalar(select(model).filter_by(**filters))
                if item is None:
                    item = model(id=str(uuid4()), **filters, **values)
                    s.add(item)
                    await s.flush()
                return item

            dep = await get_or_create(
                DepartamentoModel, {"empresa_id": empresa.id, "nombre": "[SPRINT2 DEMO] Tecnologia"}
            )
            cargo = await get_or_create(
                CargoModel,
                {"empresa_id": empresa.id, "nombre": "[SPRINT2 DEMO] Backend"},
                departamento_id=dep.id,
            )
            vacancy = await get_or_create(
                VacanteModel,
                {"empresa_id": empresa.id, "titulo": "[SPRINT2 DEMO] Backend Python"},
                cargo_id=cargo.id,
                departamento_id=dep.id,
                responsable_id=user.id,
                descripcion="Synthetic Python/PostgreSQL selection demo",
                requisitos="Python, SQL, REST APIs; 2 years experience",
                modalidad="REMOTO",
                estado="PUBLICADA",
                cantidad_vacantes=2,
                experiencia_min=2,
            )
            skills = []
            for name, weight in (("Python", 3), ("SQL", 2), ("REST APIs", 1)):
                skill = await get_or_create(
                    HabilidadModel, {"empresa_id": empresa.id, "nombre": name}, categoria="Tecnica"
                )
                await get_or_create(
                    VacanteHabilidadModel,
                    {"vacante_id": vacancy.id, "habilidad_id": skill.id},
                    nivel_requerido="INTERMEDIO",
                    peso=weight,
                    es_obligatorio=True,
                )
                skills.append(skill)
            storage = LocalCvStorage()
            posts, candidates, interviews = [], [], []
            for n, name in enumerate(("Ana", "Luis", "Maria")):
                candidate = await get_or_create(
                    PostulanteModel,
                    {"empresa_id": empresa.id, "ci": f"SPRINT2-DEMO-{n + 1}"},
                    nombres=name,
                    apellidos="Demo",
                    email=f"sprint2-{n + 1}@example.invalid",
                    telefono="00000000",
                    ciudad="La Paz",
                    nivel_educativo="LICENCIATURA",
                    fuente="OTRO",
                    anios_experiencia=n + 2,
                    en_banco_talento=True,
                    cv_texto=f"Synthetic CV: {name} Demo. Python SQL REST. {n + 2} years experience.",
                )
                post = await get_or_create(
                    PostulacionModel,
                    {"vacante_id": vacancy.id, "postulante_id": candidate.id},
                    etapa_id=initial.id,
                    estado="ACTIVA",
                    codigo_seguimiento="DEMO-" + uuid4().hex,
                    puntaje_ia=(90, 75, 60)[n],
                    puntaje_manual=(85, 70, 65)[n],
                )
                posts.append(post.id)
                candidates.append(candidate.id)
                if candidate.cv_url is None or storage.resolve_cv(candidate.cv_url) is None:
                    pdf_bytes = BytesIO()
                    pdf = canvas.Canvas(pdf_bytes, pagesize=(595, 842), invariant=True)
                    pdf.setTitle("Synthetic Sprint2 CV")
                    lines = [
                        f"{name} Demo - SYNTHETIC CV",
                        "Not a real candidate. Local testing only.",
                        f"Experience: {n + 2} years Python, PostgreSQL / SQL, REST APIs.",
                        "Education: Bachelor degree in software engineering.",
                        "Built REST APIs using Python and PostgreSQL; wrote SQL queries.",
                    ]
                    for index, line in enumerate(lines):
                        pdf.drawString(48, 790 - index * 24, line)
                    pdf.save()
                    candidate.cv_url = await storage.save_cv(
                        CvAdjunto(
                            filename="synthetic-demo.pdf",
                            content_type="application/pdf",
                            content=pdf_bytes.getvalue(),
                        ),
                        post.codigo_seguimiento,
                    )
                if not storage.owns_cv(candidate.cv_url, [post.codigo_seguimiento]):
                    raise ValueError(
                        "Demo CV ownership does not match the application tracking code"
                    )
                for skill in skills:
                    await get_or_create(
                        PostulanteHabilidadModel,
                        {"postulante_id": candidate.id, "habilidad_id": skill.id},
                        nivel="INTERMEDIO",
                        anios_experiencia=n + 2,
                        detectado_por_ia=False,
                    )
                await get_or_create(
                    AnalisisCvModel,
                    {"postulacion_id": post.id, "modelo_usado": "synthetic-demo-no-provider"},
                    puntaje_afinidad=(90, 75, 60)[n],
                    habilidades_detectadas=["Python", "SQL"],
                    habilidades_faltantes=["Rust"],
                    fortalezas=["SQL"],
                    anios_experiencia_detectados=n + 2,
                    resumen_ia="Synthetic fixture; no external provider",
                    tiempo_proceso_ms=0,
                )
                assessment = await get_or_create(
                    EvaluacionModel,
                    {"postulacion_id": post.id, "nombre": "[SPRINT2 DEMO] SQL"},
                    evaluador_id=user.id,
                    tipo="TECNICA",
                    puntaje=(18, 15, 12)[n],
                    puntaje_maximo=20,
                    aprobado=True,
                    observaciones="Synthetic demo evaluation; no provider",
                )
                if assessment.observaciones is None:
                    assessment.observaciones = "Synthetic demo evaluation; no provider"
                appointment = await get_or_create(
                    EntrevistaModel,
                    {"postulacion_id": post.id, "lugar": f"SPRINT2 DEMO {n + 1}"},
                    entrevistador_id=user.id,
                    tipo="TELEFONICA" if n == 1 else "TECNICA",
                    modalidad="TELEFONICA" if n == 1 else "VIRTUAL",
                    enlace_reunion="" if n == 1 else "https://example.invalid/demo",
                    fecha_hora=datetime.now(UTC) + timedelta(days=n + 1),
                    duracion_min=45,
                    estado="PROGRAMADA",
                )
                interviews.append(appointment.id)
            manifest = {
                "empresa_slug": empresa.slug,
                "empresa_id": empresa.id,
                "user_id": user.id,
                "vacante_id": vacancy.id,
                "postulacion_ids": posts,
                "postulante_ids": candidates,
                "entrevista_ids": interviews,
            }
            if args.session_file:
                from ssas.core.security.jwt import JWTService
                from ssas.roles.infrastructure.persistence.models.role import RoleModel
                from ssas.roles.infrastructure.persistence.models.user_role import usuario_rol_table

                roles = (
                    await s.scalars(
                        select(RoleModel.codigo)
                        .join(usuario_rol_table, usuario_rol_table.c.rol_id == RoleModel.id)
                        .where(
                            usuario_rol_table.c.usuario_id == user.id,
                            RoleModel.empresa_id == empresa.id,
                        )
                    )
                ).all()
                manifest["access_token"] = JWTService().create_access_token(
                    user.id, empresa.id, roles=list(roles)
                )
                if created_admin:
                    manifest["local_demo_login"] = {
                        "username": os.environ.get("SPRINT2_DEMO_ADMIN_USERNAME", ""),
                        "password": os.environ["SPRINT2_DEMO_ADMIN_PASSWORD"],
                        "empresa_slug": empresa.slug,
                    }
            await s.commit()
            if args.session_file:
                args.session_file.parent.mkdir(parents=True, exist_ok=True)
                args.session_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                print("Local disposable session written; token is not logged.")
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in manifest.items()
                        if k not in {"access_token", "local_demo_login"}
                    },
                    indent=2,
                )
            )
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--empresa-slug", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-empresa-slug")
    parser.add_argument("--create-empresa", action="store_true")
    parser.add_argument("--session-file", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]{2,120}", args.empresa_slug):
        parser.error("Use a lowercase company slug")
    if args.apply and args.confirm_empresa_slug != args.empresa_slug:
        parser.error("Writes require --confirm-empresa-slug identical to --empresa-slug")
    if args.session_file and args.session_file.suffix.lower() != ".json":
        parser.error("--session-file must be a temporary JSON file; never commit it")
    configure()
    try:
        asyncio.run(cargar(args))
    except Exception as exc:  # noqa: BLE001 - prevent credentials in validation/SQL tracebacks
        # Validation/SQL exceptions can contain supplied passwords or bound values.
        print(
            f"Demo aborted ({type(exc).__name__}); verify provisioning inputs/catalog/subscription. No credentials logged.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
