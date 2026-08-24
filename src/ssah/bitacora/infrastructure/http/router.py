from fastapi import APIRouter

router = APIRouter(prefix="/bitacora", tags=["bitacora"])


@router.get("/health")
async def bitacora_health() -> dict[str, str]:
    return {"status": "ok"}
