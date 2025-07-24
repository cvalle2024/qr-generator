import streamlit as st
import random

# === Configuración de la página ===
st.set_page_config(page_title="Centro ERSI", layout="centered")

# === Usuarios válidos ===
USUARIOS_VALIDOS = {
    "admin": "1234",
    "reclutador": "ersi2025"
}

# === Inicializar estado de sesión ===
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "captcha_valido" not in st.session_state:
    st.session_state.captcha_valido = False
if "num1" not in st.session_state:
    st.session_state.num1 = random.randint(1, 9)
if "num2" not in st.session_state:
    st.session_state.num2 = random.randint(1, 9)

# === Login con CAPTCHA ===
if not st.session_state.logueado:
    st.title("🔐 Iniciar sesión")

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")

    # CAPTCHA
    st.write("Verificación humana:")
    captcha_input = st.text_input(f"¿Cuánto es {st.session_state.num1} + {st.session_state.num2}?")

    if st.button("Ingresar"):
        if captcha_input.strip() == str(st.session_state.num1 + st.session_state.num2):
            st.session_state.captcha_valido = True
        else:
            st.error("❌ CAPTCHA incorrecto. Inténtalo de nuevo.")
            # Cambiar los números aleatorios
            st.session_state.num1 = random.randint(1, 9)
            st.session_state.num2 = random.randint(1, 9)
            st.stop()

        if st.session_state.captcha_valido:
            if usuario in USUARIOS_VALIDOS and clave == USUARIOS_VALIDOS[usuario]:
                st.session_state.logueado = True
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
                st.session_state.captcha_valido = False
                st.session_state.num1 = random.randint(1, 9)
                st.session_state.num2 = random.randint(1, 9)

# === Contenido de la app una vez logueado ===
else:
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
        st.session_state.clear()  # Limpia toda la sesión
        st.rerun()

