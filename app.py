import streamlit as st

st.set_page_config(page_title="Login", layout="centered")

# Redirige si ya está autenticado
if st.session_state.get("autenticado") == True:
    st.switch_page("Home")

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
    if password == "clave_ersi123":
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido")
        st.experimental_rerun()  # 👉 Esto re-ejecuta app.py y entra al if superior
    else:
        st.error("❌ Contraseña incorrecta.")

