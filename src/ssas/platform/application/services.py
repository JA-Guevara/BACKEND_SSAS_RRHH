from math import ceil


def page_payload(items: list, total: int, page: int, per_page: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page) if total else 0,
    }


def subscription_payload(model) -> dict:
    return {
        "id": model.id,
        "empresa_id": model.empresa_id,
        "empresa_nombre": model.empresa.nombre_comercial if getattr(model, "empresa", None) else None,
        "plan": model.plan,
        "fecha_inicio": model.fecha_inicio,
        "fecha_fin": model.fecha_fin,
        "activo": model.activo,
        "created_at": model.created_at,
    }


def empresa_payload(model) -> dict:
    subscriptions = [item for item in model.suscripciones if item.activo]
    active = max(subscriptions, key=lambda item: item.fecha_inicio) if subscriptions else None
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
        "activo": model.activo,
        "fecha_registro": model.fecha_registro,
        "suscripcion": subscription_payload(active) if active else None,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
