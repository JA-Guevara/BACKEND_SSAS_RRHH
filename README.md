# Backend SSAS RRHH

API multiempresa de gestión de recursos humanos desarrollada con FastAPI, SQLAlchemy y PostgreSQL.

## Inicio rápido

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn ssas.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- Estado: `http://127.0.0.1:8000/health`
- Documentación del proyecto: [docs/README.md](docs/README.md)
- Guía completa de desarrollo: [docs/guias/GUIA_DESARROLLO.md](docs/guias/GUIA_DESARROLLO.md)

La configuración local se define en `.env` tomando `.env.example` como referencia. El archivo
`.env` contiene secretos y no debe subirse al repositorio.
