# pages/Login.py
import streamlit as st

st.set_page_config(page_title="Login", layout="centered")

# Evitar mostrar menú lateral hasta autenticación
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1cpxqw2 {visibility: hidden;}  /* menú lateral nuevo */
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🔒 Acceso al Sistema ERSI")
password = st.text_input("Ingrese la contraseña", type="password")

if st.button("Ingresar"):
    if password == "clave_ersi123":  # Cambia esta clave segura
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido")
        st.switch_page("Home")
    else:
        st.error("❌ Contraseña incorrecta.")

