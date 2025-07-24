import streamlit as st

# === CONFIGURACIÓN DE LA PÁGINA ===
st.set_page_config(page_title="Centro ERSI", layout="centered")

# === AUTENTICACIÓN SIMPLE CON CONTRASEÑA ===
def autenticar_usuario():
    st.markdown("### 🔒 Acceso restringido")
    password = st.text_input("Ingrese la contraseña para acceder al sistema", type="password")
    if password != "clave_ersi123":  # 🔐 Puedes cambiar esta contraseña por la que desees
        st.warning("⚠️ Contraseña incorrecta o vacía. Acceso denegado.")
        st.stop()

autenticar_usuario()  # ← Protege toda la aplicación desde la portada

# === INTERFAZ PRINCIPAL ===
st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
st.write("Seleccione una opción:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧾 Generar código único para Reclutadores"):
        st.switch_page("pages/1_Generador_Código_ERSI.py")

with col2:
    if st.button("🔐 Generar código QR"):
        st.switch_page("pages/2_Generador_Código_QR.py")
