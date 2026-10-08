from decimal import Decimal

import pytest

from ssas.analisis_cv.domain.analysis import (
    AnalisisCvError,
    ResultadoIA,
    calcular_afinidad,
    validar_evidencia,
)
from ssas.analisis_cv.infrastructure.providers.extraccion_local import ExtraccionLocalProvider
from ssas.config.settings import settings


@pytest.fixture
def provider():
    return ExtraccionLocalProvider(settings)


@pytest.fixture
def catalogo_prueba():
    return [
        {"habilidad_id": "h-py", "nombre": "Python"},
        {"habilidad_id": "h-sql", "nombre": "SQL"},
        {"habilidad_id": "h-doc", "nombre": "Docker"},
        {"habilidad_id": "h-java", "nombre": "Java"},
    ]


@pytest.fixture
def vacante_prueba():
    return {
        "titulo": "Desarrollador Backend",
        "descripcion": "Puesto de desarrollo con Python y base de datos SQL.",
        "habilidades": [
            {"habilidad_id": "h-py", "nombre": "Python", "peso": 5},
            {"habilidad_id": "h-sql", "nombre": "SQL", "peso": 3},
        ],
        "experiencia_min": 3,
    }


@pytest.mark.asyncio
async def test_detecta_habilidades_del_catalogo(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Desarrollador con experiencia profesional construyendo APIs en Python "
        "y gestionando bases de datos relacionales en SQL con alto rendimiento. Más de 50 caracteres."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    ids = [h.habilidad_id for h in res.habilidades]
    assert "h-py" in ids
    assert "h-sql" in ids
    assert "h-doc" not in ids
    assert len(res.habilidades) == 2


@pytest.mark.asyncio
async def test_ignora_mayusculas(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Experiencia avanzada programando en PYTHON en múltiples entornos "
        "productivos durante varios años de carrera técnica."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    ids = [h.habilidad_id for h in res.habilidades]
    assert "h-py" in ids


@pytest.mark.asyncio
async def test_no_confunde_subcadenas(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Experto en desarrollo web con Javascript y Node.js para aplicaciones "
        "modernas en la nube con frameworks reactivos."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    ids = [h.habilidad_id for h in res.habilidades]
    assert "h-java" not in ids


@pytest.mark.asyncio
async def test_sin_habilidades_devuelve_lista_vacia(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Licenciado en Administración de Empresas con experiencia en gestión "
        "de proyectos comerciales y finanzas corporativas generales."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    assert res.habilidades == []


@pytest.mark.asyncio
async def test_catalogo_vacio(provider, vacante_prueba):
    texto = (
        "Desarrollador con experiencia profesional construyendo APIs en Python "
        "y gestionando bases de datos relacionales en SQL con alto rendimiento."
    )
    res = await provider.analyze(texto, vacante_prueba, [])
    assert isinstance(res, ResultadoIA)
    assert res.habilidades == []


@pytest.mark.asyncio
async def test_evidencia_es_subcadena_literal(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Especialista en Python avanzado y bases de datos SQL relacionales. "
        "Cuenta con 4 años de experiencia en soporte y desarrollo de software."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    norm_texto = " ".join(texto.casefold().split())
    for h in res.habilidades:
        norm_evidencia = " ".join(h.evidencia.casefold().split())
        assert norm_evidencia in norm_texto


@pytest.mark.asyncio
async def test_pasa_validar_evidencia(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Especialista en Python avanzado y bases de datos SQL relacionales. "
        "Cuenta con 4 años de experiencia en soporte y desarrollo de software."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    cat_ids = {item["habilidad_id"] for item in catalogo_prueba}
    # No debe lanzar ninguna excepción
    validar_evidencia(res, cat_ids, texto)


@pytest.mark.asyncio
async def test_no_duplica_habilidades(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Programo en Python todos los días. Mi framework favorito en Python "
        "es FastAPI. Python es muy potente y versátil para ingenieros."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    ids = [h.habilidad_id for h in res.habilidades]
    assert ids.count("h-py") == 1


@pytest.mark.asyncio
async def test_experiencia_detectada(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Ingeniero de software con más de 5 años de experiencia comprobada "
        "en backend con Python y servicios distribuidos en producción."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    assert res.anios_experiencia == 5.0
    norm_texto = " ".join(texto.casefold().split())
    norm_evidencia = " ".join(res.evidencia_experiencia.casefold().split())
    assert norm_evidencia in norm_texto


@pytest.mark.asyncio
async def test_experiencia_ausente(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Recién graduado apasionado por el desarrollo web y móvil con Python "
        "buscando su primera oportunidad profesional en el área."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    assert res.anios_experiencia == 0.0
    assert res.evidencia_experiencia == ""


@pytest.mark.asyncio
async def test_texto_insuficiente_lanza_422(provider, catalogo_prueba, vacante_prueba):
    with pytest.raises(AnalisisCvError) as exc_info:
        await provider.analyze("Texto muy corto.", vacante_prueba, catalogo_prueba)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_es_determinista(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Ingeniero senior con Python y SQL, con 6 años de experiencia en proyectos "
        "de alta concurrencia y despliegues continuos."
    )
    resultados = [
        (await provider.analyze(texto, vacante_prueba, catalogo_prueba)).model_dump()
        for _ in range(5)
    ]
    primero = resultados[0]
    for r in resultados[1:]:
        assert r == primero


@pytest.mark.asyncio
async def test_resultado_valida_contra_el_esquema(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Ingeniero senior con Python y SQL, con 3 años de experiencia en proyectos "
        "de alta concurrencia y despliegues continuos en la nube."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    validado = ResultadoIA.model_validate(res.model_dump())
    assert validado.anios_experiencia == 3.0


@pytest.mark.asyncio
async def test_no_hace_peticiones_de_red(catalogo_prueba, vacante_prueba):
    prov = ExtraccionLocalProvider(settings)
    texto = (
        "Especialista con Python y SQL y 4 años de experiencia laboral en empresas "
        "de desarrollo tecnológico en Bolivia y el exterior."
    )
    # Ejecuta sin acceso a red y produce un resultado completo
    res = await prov.analyze(texto, vacante_prueba, catalogo_prueba)
    assert isinstance(res, ResultadoIA)


@pytest.mark.asyncio
async def test_afinidad_usa_la_misma_formula(provider, catalogo_prueba, vacante_prueba):
    texto = (
        "Desarrollador con Python y 3 años de experiencia en tecnología web. "
        "Texto suficiente para sobrepasar el mínimo de cincuenta caracteres."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo_prueba)
    requisitos = vacante_prueba["habilidades"]  # Python peso 5, SQL peso 3 (total 8)
    # Python acreditado: 5/8 = 0.625. Exp: 3/3 = 1.0. Afinidad: 80 * 0.625 + 20 * 1 = 50 + 20 = 70.00
    score = calcular_afinidad(requisitos, res, vacante_prueba["experiencia_min"])
    assert score == Decimal("70.00")


@pytest.mark.asyncio
async def test_sinonimos_detectan_habilidad(provider, vacante_prueba):
    catalogo = [
        {"habilidad_id": "h-pg", "nombre": "PostgreSQL"},
        {"habilidad_id": "h-ts", "nombre": "TypeScript"},
    ]
    texto = (
        "Desarrollador backend con experiencia en Postgres para sistemas "
        "de alta disponibilidad y consultas avanzadas durante años."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo)
    ids = [h.habilidad_id for h in res.habilidades]
    assert "h-pg" in ids
    assert res.habilidades[0].habilidad_id == "h-pg"


@pytest.mark.asyncio
async def test_sinonimo_ts_no_matchea_dentro_de_palabra(provider, vacante_prueba):
    catalogo = [
        {"habilidad_id": "h-ts", "nombre": "TypeScript"},
    ]
    texto = (
        "Experiencia en entornos de desarrollo con herramientas modernas "
        "de automatización y despliegue continuo de aplicaciones."
    )
    res = await provider.analyze(texto, vacante_prueba, catalogo)
    assert res.habilidades == []
