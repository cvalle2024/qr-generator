from __future__ import annotations

import streamlit as st

from app_ui import APP_VERSION, footer, hero, inject_global_styles, render_brand, render_sidebar, security_note
from auth import (
    auth_is_configured,
    authenticate,
    current_user,
    get_security_settings,
    local_auth_is_configured,
    logout,
    oidc_auth_is_configured,
    require_auth,
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
        st.error("Primero descargue la tabla de códigos generados en esta sesión antes de cerrar sesión.")
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
        "Proyecto VIHCA · Plataforma segura",
        "Identificación ERSI y generación de códigos QR",
        "Acceso controlado para crear identificadores únicos de voluntarios y materiales QR de referencia de forma consistente y trazable.",
    )

    if not auth_is_configured():
        st.error("La autenticación segura todavía no está configurada.")
        st.info(
            "Configure la autenticación en Streamlit Secrets antes de habilitar el acceso. "
            "El proyecto incluye .streamlit/secrets.example.toml y la guía SEGURIDAD_Y_DESPLIEGUE.md."
        )
        security_note("La versión 2.0 ya no acepta contraseñas escritas directamente dentro de Home.py.")
        footer("Plataforma ERSI")
        st.stop()

    # Si existe una sesión OIDC pero el correo no está autorizado, no se revela información adicional.
    oidc_browser_logged_in = False
    try:
        oidc_browser_logged_in = bool(st.user.is_logged_in)
    except Exception:
        pass

    if oidc_browser_logged_in and settings.auth_mode in {"oidc", "both"}:
        st.error("La cuenta autenticada no está autorizada para utilizar esta aplicación.")
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
            st.caption("Use su cuenta institucional configurada por el administrador.")
            if st.button("Continuar con inicio de sesión institucional", type="primary", width="stretch"):
                st.login()
        if settings.auth_mode == "both":
            st.markdown("<div style='text-align:center;color:#64748b;margin:8px 0'>o use credenciales locales autorizadas</div>", unsafe_allow_html=True)

    if settings.auth_mode in {"local", "both"} and local_auth_is_configured():
        left, center, right = st.columns([1, 1.7, 1])
        with center:
            with st.container(border=True):
                st.markdown("### Acceso con credenciales")
                st.caption("Ingrese con las credenciales autorizadas por VIHCA.")
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                    password = st.text_input("Contraseña", type="password", placeholder="••••••••••••")
                    submitted = st.form_submit_button("Ingresar de forma segura", type="primary", width="stretch")

                if submitted:
                    ok, message = authenticate(username, password)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                st.caption(
                    f"Protección activa: bloqueo tras intentos fallidos · sesión expira tras "
                    f"{settings.session_timeout_minutes} min de inactividad."
                )

    security_note(
        "Las credenciales locales se validan con hash PBKDF2 y se almacenan en Streamlit Secrets. También puede usar autenticación institucional OIDC con Google, Microsoft, Okta u otro proveedor compatible."
    )
    footer("Plataforma ERSI")
    st.stop()

# Revalida expiración de sesión y actualiza actividad.
user = require_auth()
render_sidebar(user)

with st.sidebar:
    st.divider()
    if st.button("Cerrar sesión", width="stretch"):
        cerrar_sesion()

hero(
    "Centro operativo ERSI",
    f"Bienvenido, {user.get('display_name') or user.get('username')}",
    "Seleccione el flujo de trabajo que necesita. La sesión conserva el último código ERSI para agilizar la creación del QR.",
)

if st.session_state.get("registro") and not st.session_state.get("descargado", False):
    st.warning("Tiene códigos generados sin descargar. Descargue la tabla de la sesión antes de cerrar.")

col1, col2 = st.columns(2, gap="large")
with col1:
    with st.container(border=True):
        st.markdown("### 🧬 Código ERSI")
        st.write("Genere un identificador único, registre el centro de salud y guarde el evento en Google Sheets.")
        st.caption("Incluye validación de país, sitio, datos mínimos y trazabilidad del usuario que registra.")
        if st.button("Abrir generador ERSI", type="primary", width="stretch"):
            st.switch_page("pages/1_Generador_Codigo_ERSI.py")

with col2:
    with st.container(border=True):
        st.markdown("### ▦ Código QR")
        st.write("Transforme el código ERSI en una pieza QR lista para entregar o compartir con el voluntario.")
        st.caption("Incluye clínica, contacto TBAC y diseño de salida listo para PNG.")
        if st.button("Abrir generador QR", width="stretch"):
            st.switch_page("pages/2_Generador_Codigo_QR.py")

st.markdown("#### Estado de la sesión")
a, b, c = st.columns(3)
a.metric("País asignado", user.get("pais", "—"))
b.metric("Códigos en sesión", len(st.session_state.get("registro", [])))
c.metric("Versión", APP_VERSION)

security_note("No comparta credenciales ni deje la sesión abierta en equipos de uso compartido. Use siempre Cerrar sesión al finalizar.")
footer("Plataforma ERSI")
