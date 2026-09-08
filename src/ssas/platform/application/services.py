from math import ceil


def page_payload(items: list, total: int, page: int, per_page: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page) if total else 0,
    }


def empresa_payload(model) -> dict:
    return {
        "id": model.id,
        "nit": model.nit,
        "razon_social": model.razon_social,
        "nombre_comercial": model.nombre_comercial,
        "slug": model.slug,
        "email": model.email,
        "telefono": model.telefono,
        "direccion": model.direccion,
        "ciudad": model.ciudad,
        "logo_url": model.logo_url,
        "descripcion": getattr(model, "descripcion", None),
        "color_primario": getattr(model, "color_primario", "#2563eb") or "#2563eb",
        "portal_publico_activo": getattr(model, "portal_publico_activo", True) if getattr(model, "portal_publico_activo", True) is not None else True,
        "activo": model.activo,
        "eliminado_at": model.eliminado_at,
        "eliminado_por_id": model.eliminado_por_id,
        "eliminada": model.eliminado_at is not None,
        "fecha_registro": model.fecha_registro,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
