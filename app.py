import streamlit as st

# Configuración de página
st.set_page_config(page_title="Login", layout="centered")

# Ocultar menú y footer
st.markdown("""
    <style>
    #MainMenu, footer, header, .css-1cpxqw2 {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🔒 Acceso al Sistema ERSI")

# Entrada de contraseña
password = st.text_input("Ingrese la contraseña", type="password")

if st.button("Ingresar"):
    if password == "clave_ersi123":
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido. Redirigiendo...")
        # Redirección con HTML (funciona desde raíz hacia páginas)
        st.markdown('<meta http-equiv="refresh" content="0;URL=/Home">', unsafe_allow_html=True)
    else:
        st.error("❌ Contraseña incorrecta.")
