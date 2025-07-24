# Login.py
import streamlit as st

st.set_page_config(page_title="Login ERSI", layout="centered")

# Inicializar estado de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Si ya está autenticado, ir a Home directamente
if st.session_state["autenticado"]:
    st.switch_page("Home")

# Interfaz de login
st.markdown("## 🔒 Acceso al Sistema ERSI")
st.write("Ingrese la contraseña para acceder al sistema.")

password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    if password == "clave_ersi123":  # Cambia aquí tu clave segura
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido. Redirigiendo al sistema...")
        st.switch_page("Home.py")
    else:
        st.error("❌ Contraseña incorrecta.")
