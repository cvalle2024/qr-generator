import streamlit as st
import pandas as pd
import gspread
import io
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# === VERIFICACIÓN DE SESIÓN ===
if "logueado" not in st.session_state or not st.session_state.logueado:
    st.warning("⚠️ Debe iniciar sesión para acceder.")
    st.stop()
# === PREFIJOS POR PAÍS ===
prefijos_pais = {
    "Honduras": "+504",
    "Guatemala": "+502",
    "El Salvador": "+503",
    "Panamá": "+507",
    "Nicaragua": "+505"
}
# === CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ===
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)
client = gspread.authorize(creds)
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# === CARGA DE DATOS DE CENTROS DE SALUD ===
df_centros = pd.read_csv("centros_salud_ersi.csv", encoding="latin-1")
df_centros["País"] = df_centros["País"].astype(str).str.strip()
df_centros["Departamento"] = df_centros["Departamento"].astype(str).str.strip().str.title()
df_centros["Nombre del Sitio"] = df_centros["Nombre del Sitio"].astype(str).str.strip().str.title()

# === CONFIGURACIÓN DE STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("Generador de código único para Reclutadores")
st.write("Complete el formulario para generar un código único por Reclutadores.")

if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === SELECCIÓN DE UBICACIÓN ===
# === SELECCIÓN DE UBICACIÓN ===
st.markdown("### Selección de Ubicación", False, help="En esta sección se registra la ubicación de los Servicios de Salud que reciben asistencia técnica de VIHCA")

# Obtener país del usuario en sesión
usuario_pais = st.session_state.get("pais_usuario", "").strip()
paises_disponibles = sorted(df_centros["País"].dropna().unique())

# Mostrar todos los países si el usuario es administrador ("todos")
if usuario_pais.lower() == "todos":
    paises_mostrados = paises_disponibles
else:
    paises_mostrados = [usuario_pais] if usuario_pais in paises_disponibles else []

# Selección de país (editable solo si hay más de un país a mostrar)
pais_seleccionado = st.selectbox("País", paises_mostrados, index=0, disabled=(len(paises_mostrados) == 1))

# Filtrar por país seleccionado
df_filtrado_pais = df_centros[df_centros["País"] == pais_seleccionado]
departamentos_disponibles = sorted(df_filtrado_pais["Departamento"].dropna().unique())
departamento_seleccionado = st.selectbox("Departamento", departamentos_disponibles)

# Filtrar por departamento seleccionado
df_filtrado_depto = df_filtrado_pais[df_filtrado_pais["Departamento"] == departamento_seleccionado]
sitios_disponibles = sorted(df_filtrado_depto["Nombre del Sitio"].dropna().unique())
servicio_salud = st.selectbox("Servicio de Salud", sitios_disponibles)


# === FORMULARIO PARA DATOS PERSONALES ===
with st.form("ersi_formulario"):
   
    st.markdown("### 👤 Información del Reclutador")
    st.write("*Campo obligatorio")
    iniciales = st.text_input("Ingrese las últimas 2 letras del primer nombre y del primer apellido (máx. 4 letras, ej. NALO)*", max_chars=4)
    dia = st.number_input("Día de nacimiento*", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento*", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo*", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del Reclutador*", min_value=15, max_value=100, step=1)
    generar = st.form_submit_button("Generar código único del Reclutador")

# === LÓGICA DE GENERACIÓN DE CÓDIGO ===
if generar:
    errores = []

    if not pais_seleccionado:
        errores.append("❌ El campo 'País' no puede estar vacío.")
    if not departamento_seleccionado:
        errores.append("❌ El campo 'Departamento' no puede estar vacío.")
    if not servicio_salud:
        errores.append("❌ El campo 'Servicio de Salud' no puede estar vacío.")
    if not iniciales.strip():
        errores.append("❌ El campo 'Iniciales' no puede estar vacío.")
    elif len(iniciales.strip()) > 4:
        errores.append("❌ Las iniciales deben tener máximo 4 letras.")
    if not dia:
        errores.append("❌ El campo 'Día' no puede estar vacío.")
    if not mes:
        errores.append("❌ El campo 'Mes' no puede estar vacío.")
    if not sexo:
        errores.append("❌ El campo 'Sexo' no puede estar vacío.")
    if not (15 <= edad <= 100):
        errores.append("❌ La edad debe estar entre 15 y 100 años.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        # === CONSTRUCCIÓN DEL CÓDIGO BASE ===
        pais_limpio = ''.join(pais_seleccionado.strip().split())  # Elimina espacios entre palabras
        pais_code = pais_limpio[:3].upper()  # Toma las primeras 3 letras reales

        iniciales_code = iniciales.strip().upper()
        dia_str = f"{int(dia):02}"
        mes_code = mes.upper()
        sexo_code = "H" if sexo == "Hombre" else "M"
        base = f"{pais_code}-{iniciales_code}{dia_str}{mes_code}-{sexo_code}"

        # === CÁLCULO DE CORRELATIVO ===
        try:
            existing_data = pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            st.error(f"No se pudo leer la hoja: {e}")
            existing_data = pd.DataFrame()

        if not existing_data.empty and "Código ERSI Único" in existing_data.columns:
            codigos = existing_data["Código ERSI Único"].dropna().tolist()
            correlativos = [int(re.search(r"-(\d{3})$", c).group(1)) for c in codigos if re.search(r"-(\d{3})$", c)]
            siguiente_numero = max(correlativos) + 1 if correlativos else 1
        else:
            siguiente_numero = 1

        sufijo = f"{siguiente_numero:03}"
        codigo_ersi = f"{base}-{sufijo}"
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # === GUARDAR DATOS ===
        nuevo = {
            "País": pais_seleccionado,
            "Departamento": departamento_seleccionado,
            "Servicio de Salud": servicio_salud,
            "Iniciales": iniciales_code,
            "Fecha de Nacimiento": f"{dia_str}-{mes_code}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_ersi,
            "Fecha de Registro": fecha_registro
        }

        st.session_state["registro"].append(nuevo)
        st.session_state["ultimo_ersi"] = codigo_ersi

        try:
            sheet.append_row([
                nuevo["País"],
                nuevo["Departamento"],
                nuevo["Servicio de Salud"],
                nuevo["Iniciales"],
                nuevo["Fecha de Nacimiento"],
                nuevo["Sexo"],
                nuevo["Edad"],
                nuevo["Código ERSI Único"],
                nuevo["Fecha de Registro"]
            ])
            st.success("✅ Código generado y guardado exitosamente")
        except Exception as e:
            st.warning(f"Código generado, pero no se pudo guardar en Google Sheets: {e}")

        st.code(codigo_ersi, language="text")

# === TABLA Y DESCARGA DE CÓDIGOS ===
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados en esta sesión")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        on_click=lambda: st.session_state.update({"descargado": True})
    )

st.markdown("Seleccione Generar código QR:")

if "ultimo_ersi" in st.session_state:
    if st.button("🧾 Generar código QR"):
        st.switch_page("pages/2_Generador_Código_QR.py")
else:
    st.button("🧾 Generar código QR", disabled=True)


