"""Alta de usuarios: alcance, roles obligatorios y verificación de correo.

Estas pruebas fijan el comportamiento que hacía imposible usar el módulo:
una cuenta creada por un administrador nacía con el correo sin verificar y el
login lo exige, de modo que el usuario recién creado no podía entrar nunca.
"""

import pytest

from ssas.auth.domain.exceptions import InvalidPasswordError
from ssas.usuarios.application.use_cases.crear_usuario import CrearUsuario
from ssas.usuarios.domain.exceptions import (
    InvalidRoleForEmpresaError,
    UsuarioAlreadyExistsError,
    UsuarioWithoutRoleError,
)

PASSWORD_VALIDA = "Clave.Segura.2026"


class FakeUsers:
    """Repositorio en memoria que registra con qué argumentos se creó el usuario."""

    def __init__(self, *, roles_validos: bool = True, email_ocupado: bool = False):
        self.roles_validos = roles_validos
        self.email_ocupado = email_ocupado
        self.creado: dict | None = None

    async def get_by_email(self, _email, _empresa_id):
        return object() if self.email_ocupado else None

    async def get_by_username(self, _username, _empresa_id):
        return None

    async def role_ids_belong_to_empresa(self, _role_ids, _empresa_id):
        return self.roles_validos

    async def create_usuario(self, **kwargs):
        self.creado = kwargs
        return object()


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hash:{password}"


def _caso(**kwargs):
    datos = {
        "empresa_id": "empresa-1",
        "nombre": "Ana",
        "apellido": "Pérez",
        "email": "Ana.Perez@Empresa.bo",
        "username": "AnaPerez",
        "password": PASSWORD_VALIDA,
        "role_ids": ["rol-1"],
    }
    datos.update(kwargs)
    return datos


@pytest.mark.asyncio
async def test_usuario_creado_por_administrador_nace_con_correo_verificado():
    """Sin esto la cuenta es inutilizable: el login exige el correo verificado."""
    repo = FakeUsers()
    await CrearUsuario(repo, FakeHasher()).execute(**_caso())

    assert repo.creado is not None
    assert repo.creado["email_verificado"] is True


@pytest.mark.asyncio
async def test_se_puede_exigir_verificacion_de_correo_explicitamente():
    repo = FakeUsers()
    await CrearUsuario(repo, FakeHasher()).execute(**_caso(email_verificado=False))

    assert repo.creado is not None
    assert repo.creado["email_verificado"] is False


@pytest.mark.asyncio
async def test_normaliza_correo_y_usuario_a_minusculas():
    repo = FakeUsers()
    await CrearUsuario(repo, FakeHasher()).execute(**_caso())

    assert repo.creado is not None
    assert repo.creado["email"] == "ana.perez@empresa.bo"
    assert repo.creado["username"] == "anaperez"


@pytest.mark.asyncio
async def test_sin_roles_no_se_crea():
    repo = FakeUsers()
    with pytest.raises(UsuarioWithoutRoleError):
        await CrearUsuario(repo, FakeHasher()).execute(**_caso(role_ids=[]))
    assert repo.creado is None


@pytest.mark.asyncio
async def test_rol_de_otro_alcance_no_se_acepta():
    """Un rol de otra empresa (o global) no puede asignarse a un usuario de empresa."""
    repo = FakeUsers(roles_validos=False)
    with pytest.raises(InvalidRoleForEmpresaError):
        await CrearUsuario(repo, FakeHasher()).execute(**_caso())
    assert repo.creado is None


@pytest.mark.asyncio
async def test_correo_repetido_en_el_mismo_alcance_no_se_acepta():
    repo = FakeUsers(email_ocupado=True)
    with pytest.raises(UsuarioAlreadyExistsError):
        await CrearUsuario(repo, FakeHasher()).execute(**_caso())
    assert repo.creado is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password",
    [
        "Corta.1a",  # menos de 12 caracteres
        "clave.segura.2026",  # sin mayúscula
        "CLAVE.SEGURA.2026",  # sin minúscula
        "Clave.Segura.Bien",  # sin número
        "ClaveSegura2026",  # sin carácter especial
        "Clave Segura 2026!",  # con espacios
        "AnaPerez.2026x",  # contiene el nombre de usuario
    ],
)
async def test_contrasena_debe_cumplir_la_politica(password):
    """La interfaz replica esta política: cualquier divergencia rompe el alta."""
    repo = FakeUsers()
    with pytest.raises(InvalidPasswordError):
        await CrearUsuario(repo, FakeHasher()).execute(**_caso(password=password))
    assert repo.creado is None


@pytest.mark.asyncio
async def test_administrador_de_plataforma_se_crea_sin_empresa():
    """`empresa_id=None` es exactamente la vía para crear un superusuario."""
    repo = FakeUsers()
    await CrearUsuario(repo, FakeHasher()).execute(**_caso(empresa_id=None))

    assert repo.creado is not None
    assert repo.creado["empresa_id"] is None


class TestContratoDeAlta:
    """El formulario del frontend replica estas reglas: si divergen, el alta falla."""

    def test_email_verificado_es_verdadero_por_omision(self):
        from ssas.usuarios.infrastructure.http.schemas import CrearUsuarioRequest

        peticion = CrearUsuarioRequest(
            nombre="Ana",
            apellido="Pérez",
            email="ana@empresa.bo",
            username="anaperez",
            password=PASSWORD_VALIDA,
            role_ids=["rol-1"],
        )
        assert peticion.email_verificado is True

    def test_exige_al_menos_un_rol(self):
        from pydantic import ValidationError

        from ssas.usuarios.infrastructure.http.schemas import CrearUsuarioRequest

        with pytest.raises(ValidationError) as excinfo:
            CrearUsuarioRequest(
                nombre="Ana",
                apellido="Pérez",
                email="ana@empresa.bo",
                username="anaperez",
                password=PASSWORD_VALIDA,
                role_ids=[],
            )
        assert any(error["loc"] == ("role_ids",) for error in excinfo.value.errors())

    def test_exige_contrasena_de_doce_caracteres(self):
        from pydantic import ValidationError

        from ssas.usuarios.infrastructure.http.schemas import CrearUsuarioRequest

        with pytest.raises(ValidationError) as excinfo:
            CrearUsuarioRequest(
                nombre="Ana",
                apellido="Pérez",
                email="ana@empresa.bo",
                username="anaperez",
                password="Corta.1a",
                role_ids=["rol-1"],
            )
        assert any(error["loc"] == ("password",) for error in excinfo.value.errors())

    def test_empresa_id_es_opcional_para_crear_administrador_de_plataforma(self):
        from ssas.usuarios.infrastructure.http.schemas import CrearUsuarioRequest

        peticion = CrearUsuarioRequest(
            nombre="Ana",
            apellido="Pérez",
            email="ana@ssas.bo",
            username="anaperez",
            password=PASSWORD_VALIDA,
            role_ids=["rol-global"],
        )
        assert peticion.empresa_id is None
