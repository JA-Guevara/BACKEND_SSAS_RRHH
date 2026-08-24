from sqlalchemy import create_engine, text

from ssah.config.settings import settings
from ssah.core.security.hashing import hash_password

ADMIN_EMAIL = "admin@test.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"
EMPRESA_SLUG = "ssah-demo"
ROL_ADMIN_CODIGO = "ADMIN_EMPRESA"

PERMISOS = [
    ("usuarios:crear", "seguridad", "usuarios", "crear", "Permite crear usuarios dentro de la empresa"),
    ("usuarios:editar", "seguridad", "usuarios", "editar", "Permite editar usuarios dentro de la empresa"),
    ("roles:gestionar", "seguridad", "roles", "gestionar", "Permite gestionar roles y permisos de la empresa"),
    ("bitacora:ver", "seguridad", "bitacora", "ver", "Permite consultar la bitacora de auditoria de la empresa"),
    ("vacantes:gestionar", "reclutamiento", "vacantes", "gestionar", "Permite gestionar vacantes"),
    ("candidatos:gestionar", "reclutamiento", "candidatos", "gestionar", "Permite gestionar candidatos"),
    ("aprobaciones:gestionar", "administracion_personal", "aprobaciones", "gestionar", "Permite gestionar aprobaciones"),
]


def scalar(conn, statement: str, params: dict | None = None) -> str:
    value = conn.execute(text(statement), params or {}).scalar_one()
    return str(value)


def main() -> None:
    engine = create_engine(settings.database_url)
    password_hash = hash_password(ADMIN_PASSWORD)

    with engine.begin() as conn:
        plan_id = scalar(
            conn,
            """
            INSERT INTO plan_suscripcion (nombre, precio_mensual, max_empleados, modulos)
            VALUES (:nombre, 0, 50, '["seguridad", "usuarios", "roles", "bitacora", "reclutamiento"]'::jsonb)
            ON CONFLICT (nombre) DO UPDATE
            SET updated_at = now()
            RETURNING id
            """,
            {"nombre": "Plan Inicial"},
        )

        empresa_id = scalar(
            conn,
            """
            INSERT INTO empresa (nit, razon_social, nombre_comercial, slug, email, telefono, ciudad, activo)
            VALUES (:nit, :razon_social, :nombre_comercial, :slug, :email, :telefono, :ciudad, true)
            ON CONFLICT (slug) DO UPDATE
            SET razon_social = EXCLUDED.razon_social,
                nombre_comercial = EXCLUDED.nombre_comercial,
                email = EXCLUDED.email,
                telefono = EXCLUDED.telefono,
                ciudad = EXCLUDED.ciudad,
                activo = true,
                updated_at = now()
            RETURNING id
            """,
            {
                "nit": "0000000000",
                "razon_social": "SSAH Demo S.R.L.",
                "nombre_comercial": "SSAH Demo",
                "slug": EMPRESA_SLUG,
                "email": "contacto@ssah-demo.test",
                "telefono": "70000000",
                "ciudad": "Santa Cruz",
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO suscripcion (empresa_id, plan_id, fecha_inicio, activo)
                VALUES (:empresa_id, :plan_id, CURRENT_DATE, true)
                ON CONFLICT DO NOTHING
                """
            ),
            {"empresa_id": empresa_id, "plan_id": plan_id},
        )

        permiso_ids: list[str] = []
        for codigo, modulo, recurso, operacion, descripcion in PERMISOS:
            permiso_ids.append(
                scalar(
                    conn,
                    """
                    INSERT INTO permiso (codigo, modulo, recurso, operacion, descripcion)
                    VALUES (:codigo, :modulo, :recurso, :operacion, :descripcion)
                    ON CONFLICT (codigo) DO UPDATE
                    SET modulo = EXCLUDED.modulo,
                        recurso = EXCLUDED.recurso,
                        operacion = EXCLUDED.operacion,
                        descripcion = EXCLUDED.descripcion,
                        updated_at = now()
                    RETURNING id
                    """,
                    {
                        "codigo": codigo,
                        "modulo": modulo,
                        "recurso": recurso,
                        "operacion": operacion,
                        "descripcion": descripcion,
                    },
                )
            )

        rol_id = scalar(
            conn,
            """
            INSERT INTO rol (empresa_id, nombre, codigo, descripcion, es_base, activo)
            VALUES (:empresa_id, :nombre, :codigo, :descripcion, true, true)
            ON CONFLICT (empresa_id, codigo) DO UPDATE
            SET nombre = EXCLUDED.nombre,
                descripcion = EXCLUDED.descripcion,
                es_base = true,
                activo = true,
                updated_at = now()
            RETURNING id
            """,
            {
                "empresa_id": empresa_id,
                "nombre": "Administrador de Empresa",
                "codigo": ROL_ADMIN_CODIGO,
                "descripcion": "Acceso administrativo completo para la empresa",
            },
        )

        for permiso_id in permiso_ids:
            conn.execute(
                text(
                    """
                    INSERT INTO rol_permiso (rol_id, permiso_id)
                    VALUES (:rol_id, :permiso_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"rol_id": rol_id, "permiso_id": permiso_id},
            )

        user_id = scalar(
            conn,
            """
            INSERT INTO usuario (
                empresa_id, nombre, apellido, email, username, password_hash,
                telefono, activo, email_verified, debe_cambiar_password
            )
            VALUES (
                :empresa_id, :nombre, :apellido, :email, :username, :password_hash,
                :telefono, true, true, false
            )
            ON CONFLICT (empresa_id, email) DO UPDATE
            SET nombre = EXCLUDED.nombre,
                apellido = EXCLUDED.apellido,
                username = EXCLUDED.username,
                password_hash = EXCLUDED.password_hash,
                telefono = EXCLUDED.telefono,
                activo = true,
                email_verified = true,
                debe_cambiar_password = false,
                updated_at = now()
            RETURNING id
            """,
            {
                "empresa_id": empresa_id,
                "nombre": "Admin",
                "apellido": "Demo",
                "email": ADMIN_EMAIL,
                "username": ADMIN_USERNAME,
                "password_hash": password_hash,
                "telefono": "70000001",
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO usuario_rol (usuario_id, rol_id, asignado_por_id)
                VALUES (:usuario_id, :rol_id, NULL)
                ON CONFLICT DO NOTHING
                """
            ),
            {"usuario_id": user_id, "rol_id": rol_id},
        )

    print("Seed de desarrollo aplicado correctamente")
    print(f"empresa_slug={EMPRESA_SLUG}")
    print(f"admin_email={ADMIN_EMAIL}")
    print(f"admin_username={ADMIN_USERNAME}")
    print(f"admin_password={ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()