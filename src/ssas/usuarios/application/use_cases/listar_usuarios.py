from math import ceil


class ListarUsuarios:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, empresa_id: str, search: str | None, is_active: bool | None, page: int, per_page: int) -> dict:
        items, total = await self.repository.list_usuarios(empresa_id, search, is_active, page, per_page)
        return {"items": items, "total": total, "page": page, "per_page": per_page, "total_pages": ceil(total / per_page) if total else 0}
