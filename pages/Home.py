import streamlit as st

# Configurar página (título debe coincidir con switch_page("Home"))
st.set_page_config(page_title="Home", layout="centered")

# Verificar autenticación
if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
    st.switch_page("Login")

# Contenido principal
st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
st.write("Seleccione una opción:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧾 Generar Código ERSI"):
        st.switch_page("1_Generador_Código_ERSI")

with col2:
    if st.button("🔐 Generar Código QR"):
        st.switch_page("2_Generador_Código_QR")
