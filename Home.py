import streamlit as st

# === Configuración de la página ===
st.set_page_config(page_title="Centro ERSI", layout="centered")

# === Login simple ===
# Puedes reemplazar estos valores por usuarios desde una base de datos si lo deseas
USUARIOS_VALIDOS = {
    "admin": "1234",
    "reclutador": "ersi2025"
}

# Inicializar estado de sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# === Si no ha iniciado sesión, mostrar login ===
if not st.session_state.logueado:
    st.title("🔐 Iniciar sesión")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    login = st.button("Ingresar")

    if login:
        if usuario in USUARIOS_VALIDOS and clave == USUARIOS_VALIDOS[usuario]:
            st.session_state.logueado = True
            st.session_state.usuario = usuario
            #st.experimental_rerun()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
else:
    # === Contenido de la app una vez logueado ===
    st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
    st.write(f"Hola, **{st.session_state.usuario}**. Seleccione una opción:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧾 Generar Código ERSI"):
            st.switch_page("pages/1_Generador_Código_ERSI.py")

    with col2:
        if st.button("🔐 Generar Código QR"):
            st.switch_page("pages/2_Generador_Código_QR.py")

    # Botón para cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.logueado = False
        st.session_state.usuario = ""
        st.experimental_rerun()
