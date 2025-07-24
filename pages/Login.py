import streamlit as st

# Configurar título de página
st.set_page_config(page_title="Login", layout="centered")

# Ocultar menú y barra
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1cpxqw2 {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🔒 Acceso al Sistema ERSI")

# Entrada de contraseña
password = st.text_input("Ingrese la contraseña", type="password")

if st.button("Ingresar"):
    if password == "clave_ersi123":  # Cambia tu clave aquí
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido. Redirigiendo...")
        st.switch_page("Home")  # Esto funcionará si el título en Home.py es "Home"
    else:
        st.error("❌ Contraseña incorrecta.")


