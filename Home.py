# Home.py
import streamlit as st

st.set_page_config(page_title="Centro ERSI", layout="centered")

# Verificar si el usuario está autenticado
if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
    st.warning("⚠️ Acceso no autorizado. Por favor inicie sesión.")
    st.switch_page("Login.py")

# Contenido principal del sistema
st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
st.write("Seleccione una opción:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧾 Generar código único para Reclutadores"):
        st.switch_page("pages/1_Generador_Código_ERSI.py")

with col2:
    if st.button("🔐 Generar código QR"):
        st.switch_page("pages/2_Generador_Código_QR.py")



