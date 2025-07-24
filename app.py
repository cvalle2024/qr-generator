import streamlit as st

st.set_page_config(page_title="Login", layout="centered")

# Ocultar elementos visuales
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🔒 Acceso al Sistema ERSI")

password = st.text_input("Ingrese la contraseña", type="password")
if st.button("Ingresar"):
    if password == "@aguilanegra":
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido")
        st.switch_page("Home")
    else:
        st.error("❌ Contraseña incorrecta.")
