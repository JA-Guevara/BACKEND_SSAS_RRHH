from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.postulaciones.domain.entities.postulacion_publica import (
    DatosPostulantePublico,
    PostulacionCreada,
    PostulacionSeguimiento,
    PostulantePublico,
    VacantePublica,
)
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulaciones.ports.outgoing.postulacion_publica_repository import (
    PostulacionPublicaRepository,
)
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.infrastructure.persistence.repositories.vacante_repository import (
    condiciones_vacante_vigente,
)


class SqlAlchemyPostulacionPublicaRepository(PostulacionPublicaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_vacante(self, vacante_id: str) -> VacantePublica | None:
        """Devuelve la vacante solo si es postulable de cara al público.

        Sin el JOIN con ``empresa`` una postulación pública podía entrar en una empresa
        suspendida o borrada lógicamente, o en una vacante ya vencida.
        """
        result = await self.session.execute(
            select(VacanteModel)
            .join(EmpresaModel, EmpresaModel.id == VacanteModel.empresa_id)
            .where(VacanteModel.id == vacante_id, *condiciones_vacante_vigente())
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return VacantePublica(
            id=model.id,
            empresa_id=model.empresa_id,
            titulo=model.titulo,
            estado=model.estado,
        )

    async def get_etapa_inicial_id(self, empresa_id: str) -> str | None:
        result = await self.session.execute(
            select(EtapaReclutamientoModel.id).where(
                EtapaReclutamientoModel.empresa_id == empresa_id,
                EtapaReclutamientoModel.es_inicial.is_(True),
            ).order_by(EtapaReclutamientoModel.orden).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_postulante_by_empresa_ci(
        self, empresa_id: str, ci: str
    ) -> PostulantePublico | None:
        result = await self.session.execute(
            select(PostulanteModel).where(
                PostulanteModel.empresa_id == empresa_id,
                func.lower(PostulanteModel.ci) == ci.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return PostulantePublico(id=model.id, empresa_id=model.empresa_id, ci=model.ci)

    async def postulacion_exists(self, vacante_id: str, postulante_id: str) -> bool:
        result = await self.session.execute(
            select(func.count(PostulacionModel.id)).where(
                PostulacionModel.vacante_id == vacante_id,
                PostulacionModel.postulante_id == postulante_id,
            )
        )
        return result.scalar_one() > 0

    async def codigo_exists(self, codigo_seguimiento: str) -> bool:
        result = await self.session.execute(
            select(func.count(PostulacionModel.id)).where(
                PostulacionModel.codigo_seguimiento == codigo_seguimiento
            )
        )
        return result.scalar_one() > 0

    async def upsert_postulante(
        self,
        empresa_id: str,
        datos: DatosPostulantePublico,
        cv_url: str,
    ) -> PostulantePublico:
        result = await self.session.execute(
            select(PostulanteModel).where(
                PostulanteModel.empresa_id == empresa_id,
                func.lower(PostulanteModel.ci) == datos.ci.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = PostulanteModel(
                empresa_id=empresa_id,
                nombres=datos.nombres,
                apellidos=datos.apellidos,
                ci=datos.ci,
                email=datos.email,
                telefono=datos.telefono,
                ciudad=datos.ciudad,
                cv_url=cv_url,
                linkedin=datos.linkedin,
                nivel_educativo=datos.nivel_educativo,
                anios_experiencia=datos.anios_experiencia,
                fuente="PORTAL_WEB",
            )
            self.session.add(model)
        else:
            model.nombres = datos.nombres
            model.apellidos = datos.apellidos
            model.email = datos.email
            model.telefono = datos.telefono
            model.ciudad = datos.ciudad
            model.cv_url = cv_url
            model.linkedin = datos.linkedin
            model.nivel_educativo = datos.nivel_educativo
            model.anios_experiencia = datos.anios_experiencia
            model.fuente = "PORTAL_WEB"

        await self.session.flush()
        return PostulantePublico(id=model.id, empresa_id=model.empresa_id, ci=model.ci)

    async def create_postulacion(
        self,
        vacante_id: str,
        postulante_id: str,
        etapa_id: str,
        codigo_seguimiento: str,
    ) -> PostulacionCreada:
        model = PostulacionModel(
            vacante_id=vacante_id,
            postulante_id=postulante_id,
            etapa_id=etapa_id,
            codigo_seguimiento=codigo_seguimiento,
            estado="ACTIVA",
        )
        self.session.add(model)
        await self.session.flush()
        return PostulacionCreada(
            id=model.id,
            codigo_seguimiento=model.codigo_seguimiento,
            estado=model.estado,
            fecha_postulacion=model.fecha_postulacion,
        )

    async def get_by_codigo(self, codigo_seguimiento: str) -> PostulacionSeguimiento | None:
        result = await self.session.execute(
            select(PostulacionModel, EtapaReclutamientoModel.nombre, VacanteModel.titulo)
            .join(EtapaReclutamientoModel, EtapaReclutamientoModel.id == PostulacionModel.etapa_id)
            .join(VacanteModel, VacanteModel.id == PostulacionModel.vacante_id)
            .where(PostulacionModel.codigo_seguimiento == codigo_seguimiento)
        )
        row = result.one_or_none()
        if row is None:
            return None

        model, etapa_nombre, vacante_titulo = row
        return PostulacionSeguimiento(
            codigo_seguimiento=model.codigo_seguimiento,
            estado=model.estado,
            etapa=etapa_nombre,
            vacante=vacante_titulo,
            fecha_postulacion=model.fecha_postulacion,
            fecha_ultimo_cambio=model.fecha_ultimo_cambio,
        )
