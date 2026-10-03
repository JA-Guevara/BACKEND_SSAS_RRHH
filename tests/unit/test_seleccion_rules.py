from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ssas.postulaciones.domain.seleccion import (
    SeleccionError,
    transicion_entrevista,
    validar_agenda,
)
from ssas.postulaciones.infrastructure.http.seleccion_schemas import (
    CompararRequest,
    EvaluacionRequest,
)


@pytest.mark.parametrize("estado", ["CANCELADA", "REALIZADA"])
def test_terminal_interview_cannot_reopen(estado):
    with pytest.raises(SeleccionError):
        transicion_entrevista(estado, "CONFIRMADA")


def test_interview_requires_timezone_and_https():
    with pytest.raises(SeleccionError, match="zona horaria"):
        validar_agenda(
            datetime(2027, 1, 1, tzinfo=UTC).replace(tzinfo=None),
            "VIRTUAL",
            "https://example.test",
            "",
        )
    with pytest.raises(SeleccionError, match="HTTPS"):
        validar_agenda(datetime(2027, 1, 1, tzinfo=UTC), "VIRTUAL", "javascript:alert(1)", "")


def test_evaluation_cannot_exceed_its_scale():
    with pytest.raises(ValidationError):
        EvaluacionRequest(
            tipo="TECNICA", nombre="Prueba", puntaje=11, puntaje_maximo=10, aprobado=True
        )


def test_comparator_requires_distinct_finalists():
    candidate = uuid4()
    with pytest.raises(ValidationError):
        CompararRequest(postulacion_ids=[candidate, candidate])
