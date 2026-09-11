from __future__ import annotations

import streamlit as st

from app_ui import (
    APP_VERSION,
    footer,
    hero,
    inject_global_styles,
    notice,
    render_brand,
    render_sidebar,
    security_note,
    stats,
)
from auth import (
    auth_is_configured,
    authenticate,
    change_own_password,
    current_user,
    get_security_settings,
    local_auth_is_configured,
    logout,
    oidc_auth_is_configured,
    require_auth,
    validate_password_strength,
)

st.set_page_config(
    page_title="Plataforma ERSI | VIHCA",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_global_styles()


def cerrar_sesion() -> None:
    if st.session_state.get("registro") and not st.session_state.get("descargado", False):
        notice(
            "Antes de cerrar sesión, descargue la tabla con los códigos generados durante esta sesión.",
            "warning",
        )
        return
    logout()
    st.rerun()


settings = get_security_settings()
user = current_user()

if not user:
    render_sidebar()
    col_logo, _ = st.columns([1.2, 2.8])
    with col_logo:
        render_brand()

    hero(
        "Proyecto VIHCA · Acceso protegido",
        "Plataforma ERSI y generación de códigos QR",
        "Gestione identificadores ERSI y materiales QR desde un entorno controlado, trazable y preparado para trabajo regional.",
    )

    if not auth_is_configured():
        notice("La autenticación segura todavía no está configurada.", "danger")
        notice(
            "Configure los usuarios en Streamlit Secrets. Después podrá migrarlos al panel de administración sin guardar contraseñas en el código.",
            "info",
        )
        security_note("Las contraseñas nunca deben escribirse directamente dentro de Home.py ni subirse al repositorio.")
        footer("Plataforma ERSI")
        st.stop()

    oidc_browser_logged_in = False
    try:
        oidc_browser_logged_in = bool(st.user.is_logged_in)
    except Exception:
        pass

    if oidc_browser_logged_in and settings.auth_mode in {"oidc", "both"}:
        notice("La cuenta autenticada no está autorizada para utilizar esta aplicación.", "danger")
        if st.button("Cerrar cuenta autenticada", width="stretch"):
            try:
                st.logout()
            except Exception:
                st.session_state.clear()
                st.rerun()
        footer("Plataforma ERSI")
        st.stop()

    if settings.auth_mode in {"oidc", "both"} and oidc_auth_is_configured():
        with st.container(border=True):
            st.markdown("### Acceso institucional")
            st.caption("Utilice la cuenta institucional autorizada por el administrador.")
            if st.button("Continuar con cuenta institucional", type="primary", width="stretch"):
                st.login()
        if settings.auth_mode == "both":
            st.markdown(
                "<div style='text-align:center;color:#526277;margin:10px 0'>o ingrese con credenciales locales autorizadas</div>",
                unsafe_allow_html=True,
            )

    if settings.auth_mode in {"local", "both"} and local_auth_is_configured():
        left, center, right = st.columns([1, 1.75, 1])
        with center:
            with st.container(border=True):
                st.markdown("### Inicio de sesión")
                st.caption("Ingrese sus credenciales autorizadas por Proyecto VIHCA.")
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                    password = st.text_input("Contraseña", type="password", placeholder="••••••••••••")
                    submitted = st.form_submit_button("Ingresar", type="primary", width="stretch")

                if submitted:
                    ok, message = authenticate(username, password)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                st.caption(
                    f"Protección activa: bloqueo por intentos fallidos · sesión expira tras "
                    f"{settings.session_timeout_minutes} min de inactividad."
                )

    security_note(
        "Las contraseñas locales se validan mediante PBKDF2-SHA256. El sistema también está preparado para autenticación institucional OIDC."
    )
    footer("Plataforma ERSI")
    st.stop()

user = require_auth()
render_sidebar(user)

with st.sidebar:
    st.divider()
    if str(user.get("role", "user")).lower() == "admin":
        if st.button("⚙️ Administrar usuarios", width="stretch"):
            st.switch_page("pages/3_Administracion_Usuarios.py")
    if st.button("Cerrar sesión", width="stretch"):
        cerrar_sesion()

# Un usuario creado desde el panel puede recibir una contraseña temporal.
if user.get("must_change_password") and user.get("source") == "managed":
    hero(
        "Seguridad de la cuenta",
        "Cambie su contraseña temporal",
        "Antes de continuar, establezca una contraseña personal. La contraseña temporal dejará de ser válida inmediatamente.",
    )
    with st.form("force_password_change"):
        new_password = st.text_input("Nueva contraseña", type="password")
        confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
        save_password = st.form_submit_button("Guardar nueva contraseña", type="primary", width="stretch")
    if save_password:
        valid, message = validate_password_strength(new_password)
        if not valid:
            st.error(message)
        elif new_password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        else:
            ok, message = change_own_password(user["username"], new_password)
            if ok:
                st.success("Contraseña actualizada. Ya puede utilizar la plataforma.")
                st.rerun()
            else:
                st.error(message)
    security_note("Use una contraseña de al menos 12 caracteres con mayúscula, minúscula, número y símbolo.")
    footer("Plataforma ERSI")
    st.stop()

hero(
    "Centro operativo ERSI",
    f"Bienvenido, {user.get('display_name') or user.get('username')}",
    "Seleccione el módulo que necesita. El último código ERSI generado permanece disponible durante la sesión para agilizar la creación del QR.",
)

if st.session_state.get("registro") and not st.session_state.get("descargado", False):
    notice(
        "Tiene códigos generados pendientes de descarga. Guarde la tabla de la sesión antes de cerrar.",
        "warning",
    )

col1, col2 = st.columns(2, gap="large")
with col1:
    with st.container(border=True):
        st.markdown("### 🧬 Generador ERSI")
        st.write("Cree el identificador único del voluntario y registre el evento en la hoja central.")
        st.caption("Incluye validación de país, servicio de salud, datos mínimos y trazabilidad del usuario que registra.")
        if st.button("Abrir generador ERSI", type="primary", width="stretch"):
            st.switch_page("pages/1_Generador_Codigo_ERSI.py")

with col2:
    with st.container(border=True):
        st.markdown("### ▦ Generador QR")
        st.write("Convierta el código ERSI en una tarjeta QR lista para entregar, imprimir o compartir.")
        st.caption("Incluye clínica, contacto TBAC, prefijo del país y archivo PNG de alta legibilidad.")
        if st.button("Abrir generador QR", type="primary", width="stretch"):
            st.switch_page("pages/2_Generador_Codigo_QR.py")

if str(user.get("role", "user")).lower() == "admin":
    st.write("")
    with st.container(border=True):
        c_text, c_action = st.columns([2.4, 1])
        with c_text:
            st.markdown("### ⚙️ Administración del sistema")
            st.write("Cree y administre usuarios, asigne país y rol, restablezca contraseñas y consulte la bitácora de actividad.")
            st.caption("Disponible únicamente para cuentas con rol Administrador.")
        with c_action:
            st.write("")
            if st.button("Abrir administración", type="primary", width="stretch"):
                st.switch_page("pages/3_Administracion_Usuarios.py")

st.markdown("#### Estado de la sesión")
stats(
    [
        ("País asignado", user.get("pais", "—")),
        ("Códigos en sesión", str(len(st.session_state.get("registro", [])))),
        ("Versión", APP_VERSION),
    ]
)

security_note("No comparta credenciales ni deje la sesión abierta en equipos de uso compartido. Cierre sesión al finalizar.")
footer("Plataforma ERSI")
