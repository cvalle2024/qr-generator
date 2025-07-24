# app.py (el archivo que se ejecutará primero)
import streamlit as st

# Inicializa sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Redirige al login si no ha iniciado sesión
if not st.session_state["autenticado"]:
    st.switch_page("Login")
else:
    st.switch_page("Home")
