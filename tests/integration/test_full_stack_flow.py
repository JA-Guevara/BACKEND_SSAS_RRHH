"""Real HTTP/SQL regression on the dedicated local QA database only."""
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    os.getenv("QA_INTEGRATION") != "1",
    reason="Requires explicitly configured isolated QA database",
)


def test_company_recruitment_flow(monkeypatch, tmp_path):
    from ssas.config.settings import settings
    from ssas.core.security.hashing import Argon2PasswordHasher
    from ssas.main import app

    assert "127.0.0.1:55439/" in settings.database_url
    monkeypatch.chdir(tmp_path)
    connection = psycopg.connect(
        settings.database_url.replace("postgresql+psycopg://", "postgresql://"),
        autocommit=True,
    )
    marker = uuid4().hex[:10]
    user_id, role_id = str(uuid4()), str(uuid4())
    password = "Qa.Integration!48276"
    company_ids = []
    connection.execute(
        "INSERT INTO usuario (id,nombre,apellido,email,username,password_hash,email_verified) "
        "VALUES (%s,'QA','Platform',%s,%s,%s,true)",
        (user_id, f"qa-{marker}@example.com", f"qa-{marker}",
         Argon2PasswordHasher().hash(password)),
    )
    connection.execute(
        "INSERT INTO rol (id,nombre,codigo) VALUES (%s,%s,%s)",
        (role_id, f"QA {marker}", f"QA_{marker}"),
    )
    connection.execute("INSERT INTO usuario_rol (usuario_id,rol_id) VALUES (%s,%s)",
                       (user_id, role_id))
    connection.execute("INSERT INTO rol_permiso (rol_id,permiso_id) SELECT %s,id FROM permiso",
                       (role_id,))

    try:
        with TestClient(app) as client:
            def call(method, path, expected=200, token=None, **kwargs):
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                response = client.request(method, f"/api/v1{path}", headers=headers, **kwargs)
                assert response.status_code == expected, (method, path, response.status_code,
                                                          response.text[:800])
                return response.json() if response.content else None

            platform = call("POST", "/auth/login", json={
                "username": f"qa-{marker}", "password": password,
            })["access_token"]
            companies = []
            for suffix in ("a", "b"):
                slug = f"qa-{marker}-{suffix}"
                created = call("POST", "/empresas", 201, platform, json={
                    "empresa": {"razon_social": slug, "nombre_comercial": slug, "slug": slug},
                    "administrador": {"nombre": "Admin", "apellido": "QA",
                        "email": f"{slug}@example.com", "username": slug, "password": password},
                })
                company_id = created["empresa"]["id"]
                company_ids.append(company_id)
                # Email delivery is outside this test; provision verified test identities.
                connection.execute(
                    "UPDATE usuario SET email_verified=true, debe_cambiar_password=false "
                    "WHERE id=%s", (created["administrador_id"],),
                )
                token = call("POST", "/auth/login", json={
                    "username": slug, "empresa_slug": slug, "password": password,
                })["access_token"]
                companies.append((company_id, slug, token, created["administrador_id"]))

            a, slug, tenant, admin = companies[0]
            b, _, other, _ = companies[1]
            query = f"?empresa_id={a}"
            call("GET", "/usuarios", 401)
            call("GET", "/roles" + query, 403, other)
            call("GET", "/habilidades" + query, 403, other)
            call("GET", "/postulantes" + query, 403, other)
            call("GET", "/bitacora" + query, 403, other)
            dep = call("POST", "/departamentos" + query, 201, platform,
                       json={"nombre": "RRHH QA"})
            dep2 = call("POST", "/departamentos" + query, 201, platform,
                        json={"nombre": "Otro QA"})
            cargo = call("POST", "/cargos" + query, 201, platform,
                         json={"nombre": "Analista QA", "departamento_id": dep["id"]})
            call("GET", "/departamentos" + query, 403, other)
            call("POST", "/departamentos", 422, platform, json={"nombre": "Sin alcance"})
            call("POST", f"/cargos?empresa_id={b}", 422, platform,
                 json={"nombre": "Cruce QA", "departamento_id": dep["id"]})
            role = call("POST", "/roles" + query, 201, platform,
                        json={"name": "QA Viewer", "codigo": "QA_VIEWER"})
            permission = connection.execute(
                "SELECT id FROM permiso WHERE codigo='vacantes:ver'"
            ).fetchone()[0]
            call("PUT", f"/roles/{role['id']}/permissions" + query, token=platform,
                 json={"permission_ids": [str(permission)]})
            user_data = {"nombre": "Usuario", "apellido": "QA", "email": "valid@example.com",
                         "username": "valid-user", "password": password,
                         "role_ids": [role["id"]], "empresa_id": a}
            call("POST", "/usuarios", 422, platform, json={**user_data, "email": "bad@domain"})
            user = call("POST", "/usuarios", 201, platform, json=user_data)
            call("POST", "/usuarios", 409, platform, json=user_data)
            call("POST", "/usuarios", 422, platform,
                 json={**user_data, "empresa_id": b, "username": "cross-role"})
            call("PATCH", f"/usuarios/{user['id']}" + query, token=platform,
                 json={"nombre": "Actualizado"})
            assert call("GET", f"/usuarios/{user['id']}" + query, token=platform)["nombre"] == "Actualizado"
            call("PATCH", f"/usuarios/{user['id']}/desactivar" + query, token=platform)
            call("PATCH", f"/usuarios/{user['id']}/activar" + query, token=platform)
            skill = call("POST", "/habilidades" + query, 201, platform,
                         json={"nombre": "Comunicacion QA"})
            call("PUT", f"/habilidades/{skill['id']}" + query, token=platform,
                 json={"nombre": "Comunicacion actualizada"})

            values = {"titulo": "Analista RRHH QA", "descripcion": "Seleccion de personal QA",
                      "cargo_id": cargo["id"], "departamento_id": dep["id"],
                      "modalidad": "PRESENCIAL", "cantidad_vacantes": 1,
                      "fecha_cierre": (datetime.now(UTC) + timedelta(days=30)).isoformat()}
            call("POST", "/vacantes" + query, 409, platform,
                 json={**values, "departamento_id": dep2["id"]})
            vacancy = call("POST", "/vacantes" + query, 201, platform, json=values)
            assert vacancy["responsable_id"] == admin
            assert vacancy["empresa_id"] == a
            call("GET", f"/vacantes/{vacancy['id']}", 404, other)
            published = call("PATCH", f"/vacantes/{vacancy['id']}/publicar" + query,
                             token=platform)
            assert published["estado"] == "PUBLICADA"
            public = call("GET", f"/publico/{slug}/vacantes")
            assert any(v["id"] == vacancy["id"] for v in public)
            form = {"vacante_id": vacancy["id"], "nombres": "Candidato", "apellidos": "QA",
                    "ci": marker, "email": "candidate@example.com", "telefono": "70000000",
                    "ciudad": "Santa Cruz", "nivel_educativo": "LICENCIATURA",
                    "anios_experiencia": "2"}
            cv = {"cv": ("cv.pdf", b"%PDF-1.4\nQA integration CV\n%%EOF", "application/pdf")}
            application = call("POST", "/publico/postulaciones", 201, data=form, files=cv)
            call("POST", "/publico/postulaciones", 409, data=form, files=cv)
            call("GET", f"/publico/postulaciones/{application['codigo_seguimiento']}")
            board = call("GET", f"/vacantes/{vacancy['id']}/tablero", token=tenant)
            assert len(board) == 1
            candidate_id = board[0]["postulante_id"]
            call("GET", f"/postulantes/{candidate_id}", 404, other)
            call("GET", f"/postulantes/{candidate_id}/cv", 404, other)
            downloaded = client.get(f"/api/v1/postulantes/{candidate_id}/cv",
                                    headers={"Authorization": f"Bearer {tenant}"})
            assert downloaded.status_code == 200
            assert downloaded.content == cv["cv"][1]
            app_id = application["id"]
            call("PATCH", f"/postulaciones/{app_id}/puntaje", token=tenant, json={"puntaje": 80})
            call("PATCH", f"/postulaciones/{app_id}/puntaje", 422, tenant, json={"puntaje": 101})
            call("POST", f"/postulaciones/{app_id}/notas", 201, tenant,
                 json={"contenido": "Entrevista QA"})
            call("GET", f"/postulaciones/{app_id}/notas", 404, other)
            stages = call("GET", "/etapas-reclutamiento", token=tenant)
            stage = next(s for s in stages if not s["es_inicial"] and not s["es_rechazado"])
            call("PATCH", f"/postulaciones/{app_id}/etapa", token=tenant,
                 json={"etapa_id": stage["id"]})
            reasons = call("GET", "/motivos-rechazo", token=tenant)
            rejected = call("PATCH", f"/postulaciones/{app_id}/rechazar", token=tenant,
                            json={"motivo_rechazo_id": reasons[0]["id"]})
            rejected_stage = next(s for s in stages if s["es_rechazado"])
            assert rejected["estado"] == "DESCARTADA"
            assert rejected["etapa_id"] == rejected_stage["id"]
            call("PATCH", f"/postulaciones/{app_id}/etapa", 409, tenant,
                 json={"etapa_id": rejected_stage["id"]})
            restored = call("PATCH", f"/postulaciones/{app_id}/etapa", token=tenant,
                            json={"etapa_id": stage["id"]})
            assert restored["motivo_rechazo"] is None
            assert restored["estado"] == ("CONTRATADA" if stage["es_contratado"] else "ACTIVA")
            scoped_summary = call("GET", "/dashboard/resumen" + query, token=platform)
            assert scoped_summary["empresa_id"] == a
            assert scoped_summary["empresa"]["cargos"] == 1
            call("GET", "/dashboard/resumen" + query, 403, other)
            call("GET", "/dashboard/resumen", token=tenant)
            call("GET", "/bitacora", token=tenant)
            call("GET", "/modulos", token=platform)
            call("GET", f"/empresas/{a}/modulos", token=platform)
            call("PATCH", f"/vacantes/{vacancy['id']}/pausar", token=tenant)
            assert call("GET", f"/publico/{slug}/vacantes") == []
            call("PATCH", f"/vacantes/{vacancy['id']}/publicar", token=tenant)
            call("PATCH", f"/vacantes/{vacancy['id']}/cerrar", token=tenant)
            call("GET", "/publico/no-existe-qa/vacantes", 404)
            call("DELETE", f"/habilidades/{skill['id']}" + query, 204, platform)
            call("PUT", f"/departamentos/{dep2['id']}" + query, token=platform,
                 json={"nombre": "Departamento editado"})
            call("DELETE", f"/departamentos/{dep2['id']}" + query, 204, platform)
    finally:
        for company_id in company_ids:
            connection.execute("DELETE FROM postulacion WHERE vacante_id IN "
                               "(SELECT id FROM vacante WHERE empresa_id=%s)", (company_id,))
            connection.execute("DELETE FROM vacante WHERE empresa_id=%s", (company_id,))
            connection.execute("DELETE FROM cargo WHERE empresa_id=%s", (company_id,))
            connection.execute("DELETE FROM empresa WHERE id=%s", (company_id,))
        connection.execute("DELETE FROM usuario WHERE id=%s", (user_id,))
        connection.execute("DELETE FROM rol WHERE id=%s", (role_id,))
        connection.close()
