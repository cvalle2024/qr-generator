import streamlit as st

st.switch_page("Centro ERSI"), layout="centered")

st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
st.write("Seleccione una opción:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧾 Generar Código ERSI"):
        st.switch_page("pages/1_Generador_Código_ERSI.py")

with col2:
    if st.button("🔐 Generar Código QR"):
        st.switch_page("pages/2_Generador_Código_QR.py")
