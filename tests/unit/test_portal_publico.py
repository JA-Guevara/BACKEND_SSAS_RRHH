import uuid

from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.vacantes.infrastructure.http.router import _to_empresa_publica
from ssas.vacantes.infrastructure.http.schemas import EmpresaPublicaResponse


def _empresa(portal_activo: bool = True) -> EmpresaModel:
    return EmpresaModel(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        razon_social="Conecta Software S.R.L.",
        nombre_comercial="Conecta",
        slug="conecta",
        descripcion="Empresa de software",
        logo_url=None,
        color_primario="#123456",
        portal_publico_activo=portal_activo,
        activo=True,
    )


def test_empresa_publica_se_serializa_sin_error() -> None:
    perfil = _to_empresa_publica(_empresa())
    assert isinstance(perfil, EmpresaPublicaResponse)
    assert perfil.nombre == "Conecta Software S.R.L."
    assert perfil.nombre_comercial == "Conecta"
    assert perfil.slug == "conecta"
    assert perfil.portal_publico_activo is True


def test_empresa_publica_no_depende_de_un_atributo_nombre() -> None:
    """Regression: el endpoint usaba empresa.nombre, que no existe en EmpresaModel."""
    assert not hasattr(EmpresaModel, "nombre")
    assert hasattr(EmpresaModel, "razon_social")
    perfil = _to_empresa_publica(_empresa())
    assert perfil.nombre == "Conecta Software S.R.L."