import json
import os
import re
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
docs_dir = root_dir / "docs"
docs_dir.mkdir(exist_ok=True)

# 1. Load OpenAPI
with open(backend_dir / "openapi_dump.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

schemas = spec.get("components", {}).get("schemas", {})

def resolve(schema_dict):
    if not isinstance(schema_dict, dict):
        return schema_dict
    if "$ref" in schema_dict:
        name = schema_dict["$ref"].split("/")[-1]
        resolved = schemas.get(name, {})
        return resolve(resolved)
    if "allOf" in schema_dict:
        merged = {"properties": {}, "required": []}
        for item in schema_dict["allOf"]:
            res = resolve(item)
            if "properties" in res:
                merged["properties"].update(res["properties"])
            if "required" in res:
                merged["required"].extend(res["required"])
        return merged
    return schema_dict

def format_type(prop):
    if not isinstance(prop, dict):
        return "any"
    if "$ref" in prop:
        return prop["$ref"].split("/")[-1]
    t = prop.get("type", "")
    fmt = prop.get("format", "")
    if t == "array":
        items = prop.get("items", {})
        return f"Array<{format_type(items)}>"
    if fmt:
        return f"{t} ({fmt})"
    if "anyOf" in prop:
        clean = [x for x in prop["anyOf"] if x.get("type") != "null"]
        has_null = any(x.get("type") == "null" for x in prop["anyOf"])
        res = " | ".join(format_type(x) for x in clean)
        return f"{res} (opcional)" if has_null else res
    return t or "object"

# 2. Load Matrix from 02_API_ENDPOINTS.md
t02 = (backend_dir / "docs" / "02_API_ENDPOINTS.md").read_text(encoding="utf-8")
patron = re.compile(
    r"^\|\s*\**([A-Z0-9\-]+)\**\s*\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
)
matrix = {}
for line in t02.splitlines():
    m = patron.match(line.strip())
    if m and m.group(1).startswith("API-"):
        matrix[(m.group(2).strip(), m.group(3).strip())] = {
            "id": m.group(1).strip(),
            "method": m.group(2).strip(),
            "path": m.group(3).strip(),
            "modulo": m.group(4).strip(),
            "pa_cu": m.group(5).strip(),
            "estado": m.group(6).strip(),
            "alcance": m.group(7).strip(),
            "permiso": m.group(8).strip(),
            "task": m.group(9).strip()
        }

# 3. Load UI usage
with open(backend_dir / "scripts" / "auditar_uso_ui.py", "r", encoding="utf-8") as f:
    pass # we already know the mapping

# Detailed UI mapping for all 86 endpoints
# (method, path) -> (fe_api, fe_ui_component, status, notes)
trace_map = {
    # Auth
    ("POST", "/api/v1/auth/login"): ("authApi.login", "LoginPage.tsx, LoginForm.tsx", "CONECTADO_Y_USADO", "Autenticación de plataforma o empresa con slug."),
    ("POST", "/api/v1/auth/refresh"): ("authApi.refresh", "AuthProvider.tsx", "CONECTADO_Y_USADO", "Renovación automática de tokens JWT."),
    ("POST", "/api/v1/auth/logout"): ("authApi.logout", "AppLayout.tsx, AuthProvider.tsx", "CONECTADO_Y_USADO", "Cierre de sesión e invalidación de refresh token."),
    ("GET", "/api/v1/auth/me"): ("authApi.getCurrentUser", "AuthProvider.tsx", "CONECTADO_Y_USADO", "Carga inicial de identidad y permisos de sesión."),
    ("POST", "/api/v1/auth/password/change"): ("authApi.changePassword", "ChangePasswordPage.tsx", "CONECTADO_Y_USADO", "Cambio de contraseña voluntario y obligatorio."),
    ("POST", "/api/v1/auth/password/forgot"): ("authApi.forgotPassword", "ForgotPasswordPage.tsx", "CONECTADO_Y_USADO", "Solicitud de recuperación de contraseña."),
    ("POST", "/api/v1/auth/password/reset"): ("authApi.resetPassword", "ResetPasswordPage.tsx", "CONECTADO_Y_USADO", "Restablecimiento con token recibido por correo."),
    ("POST", "/api/v1/auth/email/verification/resend"): ("—", "—", "BACKEND_LISTO_SIN_UI", "Backend funcional; frontend no tiene botón para reenviar verificación."),
    ("POST", "/api/v1/auth/email/verify"): ("—", "—", "BACKEND_LISTO_SIN_UI", "Backend funcional; frontend no tiene ruta para captura de token de email."),
    ("POST", "/api/v1/auth/registro-empresa"): ("authApi.registroEmpresa", "RegisterCompanyPage.tsx", "CONECTADO_Y_USADO", "Auto-registro self-service de nueva empresa y admin inicial."),

    # Bitacora
    ("GET", "/api/v1/bitacora"): ("bitacoraApi.list", "BitacoraPage.tsx", "CONECTADO_Y_USADO", "Listado y filtros de auditoría por módulo, acción y fecha."),
    ("GET", "/api/v1/bitacora/{audit_log_id}"): ("bitacoraApi.get", "BitacoraPage.tsx (modal)", "CONECTADO_Y_USADO", "Detalle de evento con diferencias previas/nuevas JSONB."),

    # Cargos
    ("GET", "/api/v1/cargos"): ("organizacionApi.getCargos", "OrganizacionPage.tsx, CargosSection.tsx", "CONECTADO_Y_USADO", "Lista de cargos de la empresa."),
    ("POST", "/api/v1/cargos"): ("organizacionApi.crearCargo", "CargosSection.tsx", "CONECTADO_Y_USADO", "Creación de cargo con departamento y bandas salariales."),
    ("PUT", "/api/v1/cargos/{cargo_id}"): ("organizacionApi.actualizarCargo", "CargosSection.tsx", "CONECTADO_Y_USADO", "Edición de cargo existente."),
    ("DELETE", "/api/v1/cargos/{cargo_id}"): ("organizacionApi.eliminarCargo", "CargosSection.tsx", "CONECTADO_Y_USADO", "Eliminación lógica/física de cargo."),

    # Departamentos
    ("GET", "/api/v1/departamentos"): ("organizacionApi.getDepartamentos", "OrganizacionPage.tsx, DepartamentosSection.tsx", "CONECTADO_Y_USADO", "Lista jerárquica de departamentos."),
    ("POST", "/api/v1/departamentos"): ("organizacionApi.crearDepartamento", "DepartamentosSection.tsx", "CONECTADO_Y_USADO", "Creación de departamento con código y padre."),
    ("PUT", "/api/v1/departamentos/{departamento_id}"): ("organizacionApi.actualizarDepartamento", "DepartamentosSection.tsx", "CONECTADO_Y_USADO", "Edición de datos y dependencia jerárquica."),
    ("DELETE", "/api/v1/departamentos/{departamento_id}"): ("organizacionApi.eliminarDepartamento", "DepartamentosSection.tsx", "CONECTADO_Y_USADO", "Eliminación de departamento."),

    # Dashboard & Health
    ("GET", "/api/v1/dashboard/resumen"): ("dashboardApi.getDashboardResumen", "DashboardPage.tsx", "CONECTADO_Y_USADO", "Métricas y tarjetas de resumen según alcance."),
    ("GET", "/health"): ("—", "—", "BACKEND_LISTO_SIN_UI", "Endpoint de verificación de salud para DevOps / Railway."),

    # Empresas
    ("GET", "/api/v1/empresas"): ("empresasApi.list", "AltaEmpresaPage.tsx", "CONECTADO_Y_USADO", "Listado paginado de tenants para administración global."),
    ("POST", "/api/v1/empresas"): ("empresasApi.provision", "AltaEmpresaForm.tsx", "CONECTADO_Y_USADO", "Aprovisionamiento de nueva empresa y administrador."),
    ("GET", "/api/v1/empresas/{empresa_id}"): ("empresasApi.get", "ConfiguracionEmpresaPage.tsx", "CONECTADO_Y_USADO", "Consulta de perfil corporativo y branding."),
    ("PATCH", "/api/v1/empresas/{empresa_id}"): ("empresasApi.update", "ConfiguracionEmpresaPage.tsx", "CONECTADO_Y_USADO", "Actualización de datos y apariencia de la empresa."),
    ("DELETE", "/api/v1/empresas/{empresa_id}"): ("empresasApi.remove", "AltaEmpresaPage.tsx", "CONECTADO_Y_USADO", "Borrado lógico de tenant."),
    ("PATCH", "/api/v1/empresas/{empresa_id}/activar"): ("empresasApi.activate", "AltaEmpresaPage.tsx", "CONECTADO_Y_USADO", "Activación de empresa suspendida."),
    ("PATCH", "/api/v1/empresas/{empresa_id}/suspender"): ("empresasApi.suspend", "AltaEmpresaPage.tsx", "CONECTADO_Y_USADO", "Suspensión de acceso a empresa."),
    ("PATCH", "/api/v1/empresas/{empresa_id}/restaurar"): ("empresasApi.restore", "AltaEmpresaPage.tsx", "CONECTADO_Y_USADO", "Restauración de empresa borrada lógicamente."),

    # Modulos
    ("GET", "/api/v1/modulos"): ("modulosApi.catalogo", "—", "BACKEND_LISTO_SIN_UI", "Catálogo global disponible en API; la UI consulta por empresa."),
    ("GET", "/api/v1/empresas/{empresa_id}/modulos"): ("modulosApi.porEmpresa", "AccessProvider.tsx, EmpresaModulosPage.tsx", "CONECTADO_Y_USADO", "Módulos habilitados por empresa y permisos visuales."),
    ("PUT", "/api/v1/empresas/{empresa_id}/modulos"): ("modulosApi.actualizar", "EmpresaModulosPage.tsx", "CONECTADO_Y_USADO", "Habilitación/deshabilitación de módulos por empresa."),

    # Parametros Legales
    ("GET", "/api/v1/parametros-legales"): ("parametrosLegalesApi.getParametrosLegales", "ConfiguracionEmpresaPage.tsx", "CONECTADO_Y_USADO", "Lista de vigencias de parámetros legales."),
    ("POST", "/api/v1/parametros-legales"): ("parametrosLegalesApi.crearParametroLegal", "ConfiguracionEmpresaPage.tsx", "CONECTADO_Y_USADO", "Registro de aportes de ley y cargas sociales."),
    ("PUT", "/api/v1/parametros-legales/{periodo_id}"): ("parametrosLegalesApi.actualizarParametroLegal", "ConfiguracionEmpresaPage.tsx", "CONECTADO_Y_USADO", "Actualización de porcentajes de ley."),

    # Portal Publico
    ("GET", "/api/v1/publico/{empresa_slug}"): ("portalApi.getEmpresaPublica", "PortalPublicoPage.tsx", "CONECTADO_Y_USADO", "Perfil público y branding corporativo."),
    ("GET", "/api/v1/publico/{empresa_slug}/vacantes"): ("portalApi.getVacantesPublicas", "PortalPublicoPage.tsx, VacantesPublicasLista.tsx", "CONECTADO_Y_USADO", "Listado de vacantes publicadas y vigentes."),
    ("GET", "/api/v1/publico/{empresa_slug}/vacantes/{vacante_id}"): ("portalApi.getVacantePublica", "PortalPublicoPage.tsx, VacantePublicaDetalle.tsx", "CONECTADO_Y_USADO", "Detalle de vacante pública para postulación."),
    ("POST", "/api/v1/publico/postulaciones"): ("portalApi.enviarPostulacion", "PostulacionForm.tsx", "CONECTADO_Y_USADO", "Envío de postulación con carga de archivo PDF de CV."),
    ("GET", "/api/v1/publico/postulaciones/{codigo}"): ("portalApi.consultarPostulacion", "SeguimientoPostulacion.tsx", "CONECTADO_Y_USADO", "Consulta de avance y etapa con código alfanumérico."),

    # Postulantes
    ("GET", "/api/v1/postulantes"): ("postulantesApi.listarPostulantes", "PostulantesPage.tsx", "CONECTADO_Y_USADO", "Banco general de talentos de la empresa."),
    ("POST", "/api/v1/postulantes"): ("postulantesApi.crearPostulante", "PostulantesPage.tsx", "CONECTADO_Y_USADO", "Alta manual de candidato en banco de talentos."),
    ("GET", "/api/v1/postulantes/{postulante_id}"): ("postulantesApi.obtenerPostulante", "tableroApi.hydrate()", "CONECTADO_Y_USADO", "Consulta de perfil de candidato para hidratar el tablero."),
    ("GET", "/api/v1/postulantes/{postulante_id}/cv"): ("tableroApi.descargarCV", "PostulanteDetalleModal.tsx", "CONECTADO_Y_USADO", "Descarga y visualización de hoja de vida en PDF."),

    # Postulaciones & Tablero
    ("GET", "/api/v1/vacantes/{vacante_id}/tablero"): ("tableroApi.getPostulaciones", "TableroPage.tsx, TableroKanban.tsx", "CONECTADO_Y_USADO", "Carga de postulantes de la vacante organizados por etapa."),
    ("GET", "/api/v1/postulaciones"): ("tableroApi.getPostulaciones", "TableroPage.tsx", "CONECTADO_Y_USADO", "Consulta global de postulaciones."),
    ("GET", "/api/v1/etapas-reclutamiento"): ("tableroApi.getEtapas", "TableroPage.tsx, TableroKanban.tsx", "CONECTADO_Y_USADO", "Columnas del tablero Kanban con color y orden."),
    ("GET", "/api/v1/motivos-rechazo"): ("tableroApi.getMotivosRechazo", "RechazarPostulanteModal.tsx", "CONECTADO_Y_USADO", "Catálogo de motivos de rechazo para descalificación."),
    ("PATCH", "/api/v1/postulaciones/{postulacion_id}/etapa"): ("tableroApi.moverPostulacion", "TableroKanban.tsx", "CONECTADO_Y_USADO", "Cambio de etapa del postulante en el flujo."),
    ("PATCH", "/api/v1/postulaciones/{postulacion_id}/rechazar"): ("tableroApi.rechazarPostulante", "RechazarPostulanteModal.tsx", "CONECTADO_Y_USADO", "Descalificación de candidato con justificación."),
    ("PATCH", "/api/v1/postulaciones/{postulacion_id}/puntaje"): ("tableroApi.actualizarPuntajePostulante", "PostulanteDetalleModal.tsx", "CONECTADO_Y_USADO", "Calificación manual (1 a 100) en entrevista/revisión."),
    ("GET", "/api/v1/postulaciones/{postulacion_id}/notas"): ("tableroApi.getNotasPostulante", "PostulanteDetalleModal.tsx", "CONECTADO_Y_USADO", "Listado cronológico de notas internas del reclutador."),
    ("POST", "/api/v1/postulaciones/{postulacion_id}/notas"): ("tableroApi.agregarNotaPostulante", "PostulanteDetalleModal.tsx", "CONECTADO_Y_USADO", "Inserción de nota interna sobre el candidato."),

    # Roles y Permisos
    ("GET", "/api/v1/roles"): ("rolesApi.list", "RolesPage.tsx", "CONECTADO_Y_USADO", "Listado de roles de empresa y roles globales."),
    ("POST", "/api/v1/roles"): ("rolesApi.create", "RolesPage.tsx", "CONECTADO_Y_USADO", "Creación de nuevo rol corporativo."),
    ("GET", "/api/v1/roles/{role_id}"): ("rolesApi.get", "RolesPage.tsx", "CONECTADO_Y_USADO", "Consulta de detalle y permisos asignados al rol."),
    ("PATCH", "/api/v1/roles/{role_id}"): ("rolesApi.update", "RolesPage.tsx", "CONECTADO_Y_USADO", "Edición de nombre y descripción de rol."),
    ("DELETE", "/api/v1/roles/{role_id}"): ("rolesApi.remove", "RolesPage.tsx", "CONECTADO_Y_USADO", "Eliminación de rol personalizado."),
    ("PUT", "/api/v1/roles/{role_id}/permissions"): ("rolesApi.assignPermissions", "RolesPage.tsx", "CONECTADO_Y_USADO", "Guardado de matriz de permisos asignados al rol."),
    ("GET", "/api/v1/permisos"): ("rolesApi.permisos", "RolesPage.tsx", "CONECTADO_Y_USADO", "Catálogo completo de los 43 permisos asignables."),

    # Usuarios
    ("GET", "/api/v1/usuarios"): ("usuariosApi.list", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Listado de usuarios con filtros por estado y empresa."),
    ("POST", "/api/v1/usuarios"): ("usuariosApi.create", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Creación de colaborador y asignación de roles."),
    ("GET", "/api/v1/usuarios/me"): ("perfilApi.obtenerMiPerfil", "MiPerfilPage.tsx", "CONECTADO_Y_USADO", "Consulta de perfil del usuario logueado."),
    ("PATCH", "/api/v1/usuarios/me"): ("perfilApi.actualizarMiPerfil", "MiPerfilPage.tsx", "CONECTADO_Y_USADO", "Actualización de teléfono y datos personales."),
    ("GET", "/api/v1/usuarios/{usuario_id}"): ("usuariosApi.get", "ListadoUsuariosPage.tsx (modal)", "CONECTADO_Y_USADO", "Consulta de usuario para edición."),
    ("PATCH", "/api/v1/usuarios/{usuario_id}"): ("usuariosApi.update", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Modificación de datos y roles de usuario."),
    ("DELETE", "/api/v1/usuarios/{usuario_id}"): ("usuariosApi.remove", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Borrado lógico de usuario."),
    ("PATCH", "/api/v1/usuarios/{usuario_id}/activar"): ("usuariosApi.activate", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Activación de cuenta de usuario."),
    ("PATCH", "/api/v1/usuarios/{usuario_id}/desactivar"): ("usuariosApi.deactivate", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Desactivación de cuenta de usuario."),
    ("PATCH", "/api/v1/usuarios/{usuario_id}/restaurar"): ("usuariosApi.restore", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Restauración de usuario borrado."),
    ("PUT", "/api/v1/usuarios/{usuario_id}/password"): ("usuariosApi.changePassword", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Asignación de contraseña temporal por administrador."),
    ("PATCH", "/api/v1/usuarios/{usuario_id}/desbloquear"): ("usuariosApi.unlock", "ListadoUsuariosPage.tsx", "CONECTADO_Y_USADO", "Desbloqueo de cuenta tras superar intentos fallidos."),

    # Habilidades
    ("GET", "/api/v1/habilidades"): ("habilidadesApi.listarHabilidades", "HabilidadesPage.tsx, VacanteForm.tsx", "CONECTADO_Y_USADO", "Catálogo de habilidades técnicas y blandas."),
    ("POST", "/api/v1/habilidades"): ("habilidadesApi.crearHabilidad", "HabilidadesPage.tsx", "CONECTADO_Y_USADO", "Creación de nueva habilidad."),
    ("PUT", "/api/v1/habilidades/{habilidad_id}"): ("habilidadesApi.actualizarHabilidad", "HabilidadesPage.tsx", "CONECTADO_Y_USADO", "Edición de habilidad."),
    ("DELETE", "/api/v1/habilidades/{habilidad_id}"): ("—", "—", "BACKEND_LISTO_SIN_UI", "Backend implementado; frontend aún no incluye botón de borrado en HabilidadesPage."),

    # Vacantes
    ("GET", "/api/v1/vacantes"): ("vacantesApi.getVacantes", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Listado administrativo de vacantes con contadores por estado."),
    ("POST", "/api/v1/vacantes"): ("vacantesApi.crearVacante", "VacanteFormPage.tsx, VacanteForm.tsx", "CONECTADO_Y_USADO", "Creación de vacante con matriz de habilidades."),
    ("GET", "/api/v1/vacantes/{vacante_id}"): ("vacantesApi.getVacante", "VacanteFormPage.tsx, TableroPage.tsx", "CONECTADO_Y_USADO", "Carga de datos completos de vacante."),
    ("PUT", "/api/v1/vacantes/{vacante_id}"): ("vacantesApi.actualizarVacante", "VacanteFormPage.tsx, VacanteForm.tsx", "CONECTADO_Y_USADO", "Edición de requisitos, beneficios y habilidades."),
    ("DELETE", "/api/v1/vacantes/{vacante_id}"): ("vacantesApi.eliminarVacante", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Eliminación lógica de vacante."),
    ("PATCH", "/api/v1/vacantes/{vacante_id}/publicar"): ("vacantesApi.publicarVacante", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Transición a PUBLICADA y exposición en portal."),
    ("PATCH", "/api/v1/vacantes/{vacante_id}/reanudar"): ("vacantesApi.reanudarVacante", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Reanudación de vacante pausada."),
    ("PATCH", "/api/v1/vacantes/{vacante_id}/pausar"): ("vacantesApi.pausarVacante", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Pausa temporal de recepción de postulaciones."),
    ("PATCH", "/api/v1/vacantes/{vacante_id}/cerrar"): ("vacantesApi.cerrarVacante", "VacantesListPage.tsx", "CONECTADO_Y_USADO", "Cierre definitivo del proceso de selección.")
}

print(f"Mapped {len(trace_map)} trace entries. Testing match against matrix:")
matched = 0
for k in matrix:
    if k in trace_map:
        matched += 1
    else:
        print(f"Missing in trace_map: {k}")
print(f"Total matched: {matched} / {len(matrix)}")
