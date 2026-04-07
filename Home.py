import streamlit as st
import random
from datetime import datetime, timedelta

# === CONFIGURACIÓN ===
st.set_page_config(page_title="🗃️Centro ERSI", layout="centered")

def render_footer(org="VIHCA / M&E Regional", app_name="Generador código ERSI", version="v1.2.0"):
    year = datetime.now().year
    st.markdown(
        f"""
        <style>
            .footer {{
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background: rgba(120,255,255,0.92);
                border-top: 1px solid rgba(0,0,0,0.08);
                padding: 10px 18px;
                text-align: center;
                font-size: 12px;
                color: #6b7280;
                z-index: 9999;
                backdrop-filter: blur(6px);
            }}
            .footer b {{
                color: #111827;
            }}
            /* Para que el contenido no quede tapado por el footer */
            .block-container {{
                padding-bottom: 70px !important;
            }}
        </style>
        <div class="footer">
            © {year} <b>{org}</b> — {app_name} {version}. Todos los derechos reservados.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Llamada (una vez)
render_footer(org="Proyecto VIHCA", app_name="Generador de códigos ERSI", version="v1.2.0")


# === USUARIOS CON PAÍS ASIGNADO ===
USUARIOS_VALIDOS = {
    "admin_user": {"clave": "admin1589" , "pais" : "todos"},
    #USUARIOS HONDURAS
    "honduras_user": {"clave": "8585", "pais": "Honduras"},
    "copan_user" : {"clave": "copan123", "pais": "Honduras"},
    "colon_user" : {"clave": "colon123", "pais": "Honduras"},
    "paraiso_user" : {"clave": "paraiso123", "pais": "Honduras"},
    "atlantida_user" : {"clave": "atlantida123", "pais": "Honduras"},
    
    # USUARIOS GUATEMALA
    "guatemala_user": {"clave": "5656", "pais": "Guatemala"},
    "guate_user_001": {"clave": "guateuser123", "pais": "Guatemala"},
    "guate_user_002": {"clave": "guateuser234", "pais": "Guatemala"},
    "guate_user_003": {"clave": "guateuser567", "pais": "Guatemala"},
    "guate_user_004": {"clave": "guateuser891", "pais": "Guatemala"},
    "guate_user_005": {"clave": "guateuser765", "pais": "Guatemala"},
    # USUARIOS PANAMÁ
    
    "panama_user": {"clave": "9595", "pais": "Panamá"},
    #USUARIOS EL SALVADOR (11 departamentos)
    "ahuachapan_user": {"clave": "3847", "pais": "El Salvador"},
    "sonsonate_user": {"clave": "4629", "pais": "El Salvador"},
    "santa_ana_user": {"clave": "6492", "pais": "El Salvador"},
    "la_libertad_user": {"clave": "5186", "pais": "El Salvador"},
    "san_salvador_user": {"clave": "4762", "pais": "El Salvador"},
    "cuscatlan_user": {"clave": "5724", "pais": "El Salvador"},
    "la_paz_user": {"clave": "9472", "pais": "El Salvador"},
    "san_vicente_user": {"clave": "6249", "pais": "El Salvador"},
    "san_miguel_user": {"clave": "4517", "pais": "El Salvador"},
    "la_union_user": {"clave": "2194", "pais": "El Salvador"},
    "usulutan_user": {"clave": "8926", "pais": "El Salvador"},
    #USUARIOS NICARAGUA
    
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
    st.title("📲 Bienvenido al generador de códigos únicos de identificación para voluntarios y creación de QR")
    st.write(f"Hola bienvenido (a), **{st.session_state.usuario}**")
    st.write("Seleccione una opción: ⬇️")

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
