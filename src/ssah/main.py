from fastapi import FastAPI

from ssah.core.api.router import api_router

app = FastAPI(title="SSAH RRHH API")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Backend SSAH RRHH"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}