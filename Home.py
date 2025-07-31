import streamlit as st
import random

# === CONFIGURACIÓN ===
st.set_page_config(page_title="Centro ERSI", layout="centered")

# === USUARIOS CON PAÍS ASIGNADO ===
USUARIOS_VALIDOS = {
    "honduras_user": {"clave": "8585", "pais": "Honduras"},
    "guatemala_user": {"clave": "5656", "pais": "Guatemala"},
    "panama_user": {"clave": "9595", "pais": "Panamá"},
    "salvador_user": {"clave": "2552", "pais": "El Salvador"},
    "nicaragua_user": {"clave": "7575", "pais": "Nicaragua"}
    
}
if "descargado" not in st.session_state:
    st.session_state.descargado= False
if "registro" in st.session_state and st.session_state["registro"]:
    st.warning("⚠️ Debe descargar la tabla virtual antes de cerrar sesión si ha generado códigos.")

    
# === SESIÓN ===
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "verificado" not in st.session_state:
    st.session_state.verificado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "pais_usuario" not in st.session_state:
    st.session_state.pais_usuario = ""
if "codigo_verificacion" not in st.session_state:
    st.session_state.codigo_verificacion = None

# === LOGIN ===
if not st.session_state.logueado:
    st.title("🔐 Iniciar sesión")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    login = st.button("Ingresar")

    if login:
        if usuario in USUARIOS_VALIDOS and clave == USUARIOS_VALIDOS[usuario]["clave"]:
            codigo = str(random.randint(1000, 9999))
            st.session_state.codigo_verificacion = codigo
            st.session_state.usuario = usuario
            st.session_state.pais_usuario = USUARIOS_VALIDOS[usuario]["pais"]
            st.session_state.logueado = True
            st.session_state.verificado = False
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

# === VERIFICACIÓN POR CÓDIGO ===
elif st.session_state.logueado and not st.session_state.verificado:
    st.title("🔐 Verificación adicional")
    st.write("Por seguridad, ingrese el siguiente código para continuar:")
    st.code(st.session_state.codigo_verificacion, language="bash")
    codigo_ingresado = st.text_input("Código de verificación", max_chars=4)

    if st.button("Verificar"):
        if codigo_ingresado == st.session_state.codigo_verificacion:
            st.session_state.verificado = True
            st.rerun()
        else:
            st.error("Código incorrecto.")

# === CONTENIDO DE LA APP ===
elif st.session_state.verificado:
    st.title("📲 Bienvenido al generador de códigos únicos de identificación para Reclutadores y creación de QR")
    st.write(f"Hola, **{st.session_state.usuario}**. Seleccione una opción:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧾 Generar Código ERSI"):
            st.switch_page("pages/1_Generador_Código_ERSI.py")
    with col2:
        if st.button("🔐 Generar Código QR"):
            st.switch_page("pages/2_Generador_Código_QR.py")
    
    if st.button("Cerrar sesión"):
        if "registro" in st.session_state and st.session_state["registro"] and not st.session_state.descargado:
            st.error("❌ Primero debes descargar la tabla virtual antes de cerrar sesión. ")
       
        else:
            st.session_state.clear()
            st.rerun()
        #st.warning("⚠️ Debe descargar la tabla virtual antes de cerrar sesión.")
        

