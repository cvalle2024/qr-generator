import streamlit as st

st.set_page_config(page_title="Centro ERSI", layout="centered")

# === INICIALIZAR AUTENTICACIÓN EN SESIÓN ===
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# === AUTENTICACIÓN (mostrar si no está autenticado) ===
if not st.session_state["autenticado"]:
    st.markdown("### 🔒 Acceso restringido al sistema ERSI")
    password = st.text_input("Ingrese la contraseña", type="password")
    if password == "clave_ersi123":  # 🔑 Cambia esta contraseña según lo desees
        st.session_state["autenticado"] = True
        st.success("✅ Acceso concedido. Puede continuar.")
        # NO hacemos st.stop() aquí, permitimos seguir mostrando contenido
    else:
        st.stop()  # Bloquear si es incorrecto o vacío

# === INTERFAZ DEL SISTEMA (visible si autenticado) ===
if st.session_state["autenticado"]:
    st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
    st.write("Seleccione una opción:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧾 Generar código único para Reclutadores"):
            st.switch_page("pages/1_Generador_Código_ERSI.py")

    with col2:
        if st.button("🔐 Generar código QR"):
            st.switch_page("pages/2_Generador_Código_QR.py")



