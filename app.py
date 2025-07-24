import streamlit as st

st.set_page_config(page_title="Redireccionando...", layout="centered")

# Inicializa autenticación
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Mostrar redirección basada en sesión
if not st.session_state["autenticado"]:
    st.markdown("""
        <meta http-equiv="refresh" content="0; url=/Login" />
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <meta http-equiv="refresh" content="0; url=/Home" />
        """, unsafe_allow_html=True)
