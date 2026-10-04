from datetime import UTC, datetime, timedelta
from uuid import uuid4

from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
from ssas.postulaciones.infrastructure.http.entrevista_publica_router import _visible


def test_respuesta_publica_no_expone_resultados_internos() -> None:
    item = EntrevistaModel(
        id=str(uuid4()), postulacion_id=str(uuid4()), entrevistador_id=str(uuid4()),
        tipo="VIRTUAL", fecha_hora=datetime.now(UTC) + timedelta(days=1),
        duracion_min=45, modalidad="VIRTUAL", enlace_reunion="https://example.test",
        estado="PROGRAMADA", puntaje=90, observaciones="nota interna",
    )
    response = _visible(item).model_dump()
    assert response["estado"] == "PROGRAMADA"
    assert response["enlace_reunion"] == "https://example.test"
    assert "observaciones" not in response
    assert "puntaje" not in response
    assert "entrevistador_id" not in response
