from sqlalchemy import create_engine, text

from ssah.config.settings import settings

PARAMETER_PERMISSIONS = [
    ("parametros:ver", "configuracion", "parametros", "ver", "Permite consultar parámetros de empresa"),
    ("parametros:editar", "configuracion", "parametros", "editar", "Permite actualizar parámetros de empresa"),
]

PARAMETROS_LEGALES = [
    ("AFP_APORTE_LABORAL", "Aporte laboral AFP", "Porcentaje de aporte laboral a AFP", "porcentaje"),
    ("APORTE_SOLIDARIO", "Aporte solidario", "Parámetro de aporte solidario", "porcentaje"),
    ("RC_IVA", "RC-IVA", "Parámetro del régimen complementario al IVA", "porcentaje"),
    ("AGUINALDO", "Aguinaldo", "Parámetro configurable para cálculo de aguinaldo", "monto"),
    ("PRIMA", "Prima", "Parámetro configurable para cálculo de prima", "monto"),
]


def main() -> None:
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        admin_role_id = conn.execute(
            text("select id from rol where codigo = :codigo limit 1"),
            {"codigo": "ADMIN_EMPRESA"},
        ).scalar_one()

        for codigo, modulo, recurso, operacion, descripcion in PARAMETER_PERMISSIONS:
            permiso_id = conn.execute(
                text(
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
                    """
                ),
                {
                    "codigo": codigo,
                    "modulo": modulo,
                    "recurso": recurso,
                    "operacion": operacion,
                    "descripcion": descripcion,
                },
            ).scalar_one()
            conn.execute(
                text(
                    """
                    INSERT INTO rol_permiso (rol_id, permiso_id)
                    VALUES (:rol_id, :permiso_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"rol_id": admin_role_id, "permiso_id": permiso_id},
            )

        for codigo, nombre, descripcion, tipo_valor in PARAMETROS_LEGALES:
            conn.execute(
                text(
                    """
                    INSERT INTO parametro_legal (pais, codigo, nombre, descripcion, tipo_valor, activo)
                    VALUES ('Bolivia', :codigo, :nombre, :descripcion, :tipo_valor, true)
                    ON CONFLICT (pais, codigo) DO UPDATE
                    SET nombre = EXCLUDED.nombre,
                        descripcion = EXCLUDED.descripcion,
                        tipo_valor = EXCLUDED.tipo_valor,
                        activo = true,
                        updated_at = now()
                    """
                ),
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "tipo_valor": tipo_valor,
                },
            )

    print("Seed técnico de parámetros aplicado correctamente")
    print("permisos=parametros:ver,parametros:editar")
    print("catalogo=AFP_APORTE_LABORAL,APORTE_SOLIDARIO,RC_IVA,AGUINALDO,PRIMA")


if __name__ == "__main__":
    main()