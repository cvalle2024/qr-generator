import streamlit as st

st.set_page_config(page_title="Login", layout="centered")

st.markdown("""
    <style>
    #MainMenu, footer, header, .css-1cpxqw2 {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🔒 Acceso al Sistema ERSI")
password = st.text_input("Ingrese la contraseña", type="password")

if st.button("Ingresar"):
    if password == "clave_ersi123":
        st.session_state["autenticado"] = True
        st.session_state["pagina"] = "home"
        st.experimental_rerun()
    else:
        st.error("❌ Contraseña incorrecta.")

# Si ya autenticado, mostrar opciones
if st.session_state.get("autenticado") and st.session_state.get("pagina") == "home":
    st.success("✅ Acceso concedido.")
    st.markdown("### ¿Qué desea hacer?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧾 Generar Código ERSI"):
            st.session_state["pagina"] = "ersi"
            st.experimental_rerun()
    with col2:
        if st.button("🔐 Generar Código QR"):
            st.session_state["pagina"] = "qr"
            st.experimental_rerun()

# Navegación controlada
if st.session_state.get("pagina") == "ersi":
    st.switch_page("pages/1_Generador_Código_ERSI.py")

elif st.session_state.get("pagina") == "qr":
    st.switch_page("pages/2_Generador_Código_QR.py")

