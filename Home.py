import streamlit as st

st.set_page_config(page_title="Centro ERSI", layout="centered")

# === CONTROL DE AUTENTICACIÓN ===
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("### 🔒 Acceso restringido al sistema ERSI")
    password = st.text_input("Ingrese la contraseña", type="password")
    if password == "clave_ersi123":  # Cambia esta clave según necesidad
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido.")
        st.experimental_rerun()
    else:
        st.stop()

# === INTERFAZ PRINCIPAL (solo visible si autenticado) ===
st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
st.write("Seleccione una opción:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧾 Generar código único para Reclutadores"):
        st.switch_page("pages/1_Generador_Código_ERSI.py")

with col2:
    if st.button("🔐 Generar código QR"):
        st.switch_page("pages/2_Generador_Código_QR.py")

