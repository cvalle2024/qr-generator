import streamlit as st
import random

# === CONFIGURACIÓN ===
st.set_page_config(page_title="Centro ERSI", layout="centered")

USUARIOS_VALIDOS = {
    "admin": "1234",
    "reclutador": "ersi2025"
}

# === SESIÓN ===
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "verificado" not in st.session_state:
    st.session_state.verificado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "codigo_verificacion" not in st.session_state:
    st.session_state.codigo_verificacion = None

# === LOGIN ===
if not st.session_state.logueado:
    st.title("🔐 Iniciar sesión")

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    login = st.button("Ingresar")

    if login:
        if usuario in USUARIOS_VALIDOS and clave == USUARIOS_VALIDOS[usuario]:
            # Crear código de verificación (ej. 4 dígitos)
            codigo = str(random.randint(1000, 9999))
            st.session_state.codigo_verificacion = codigo
            st.session_state.usuario = usuario
            st.session_state.logueado = True
            st.session_state.verificado = False
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

# === VERIFICACIÓN POR CÓDIGO ===
elif st.session_state.logueado and not st.session_state.verificado:
    st.title("🔐 Verificación adicional")

    st.write("Por seguridad, ingrese el siguiente código para continuar:")
    st.code(st.session_state.codigo_verificacion, language="bash")  # visible para pruebas
    codigo_ingresado = st.text_input("Código de verificación", max_chars=4)

    if st.button("Verificar"):
        if codigo_ingresado == st.session_state.codigo_verificacion:
            st.session_state.verificado = True
            st.rerun()
        else:
            st.error("Código incorrecto.")

# === CONTENIDO DE LA APP ===
elif st.session_state.verificado:
    st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
    st.write(f"Hola, **{st.session_state.usuario}**. Seleccione una opción:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧾 Generar Código ERSI"):
            st.switch_page("pages/1_Generador_Código_ERSI.py")

    with col2:
        if st.button("🔐 Generar Código QR"):
            st.switch_page("pages/2_Generador_Código_QR.py")

    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

