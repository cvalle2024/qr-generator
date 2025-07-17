import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import io

st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ===
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# === Cargar y limpiar datos del archivo CSV de centros ===
data = pd.read_csv("centros_salud_ersi.csv")
data['País'] = data['País'].astype(str).str.strip().str.replace("_", " ").str.title()
data['DEPARTAMENTO'] = data['DEPARTAMENTO'].astype(str).str.strip().str.replace("_", " ").str.title()
data['Nombre del Sitio'] = data['Nombre del Sitio'].astype(str).str.strip()

# Inicializar almacenamiento en sesión
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === Formulario ===
with st.form("ersi_formulario"):
    pais = st.selectbox("País", sorted(data['País'].dropna().unique()))

    departamentos = sorted(data[data['País'] == pais]['DEPARTAMENTO'].dropna().unique())
    departamento = st.selectbox("Departamento", departamentos)

    municipios = sorted(data[(data['País'] == pais) & (data['DEPARTAMENTO'] == departamento)]['Nombre del Sitio'].dropna().unique())
    municipio = st.selectbox("Municipio o Sitio de Salud", municipios)

    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)

    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if iniciales and sexo and dia and mes and (15 <= edad <= 100):
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"
        ocurrencias = sum(1 for reg in st.session_state["registro"] if base in reg["Código ERSI Base"])
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        # Guardar en memoria
        nuevo = {
            "País": pais,
            "Departamento": departamento,
            "Municipio": municipio,
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Base": codigo_base,
            "Código ERSI Único": codigo_base
        }
        st.session_state["registro"].append(nuevo)

        # Guardar en Google Sheets
        sheet.append_row(list(nuevo.values()))

        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")
        st.session_state["ultimo_ersi"] = codigo_base
    else:
        st.error("Por favor, complete todos los campos correctamente.")

# Mostrar historial generado
df = pd.DataFrame(st.session_state["registro"])
if not df.empty:
    st.markdown("### 📋 Códigos generados")
    st.dataframe(df, use_container_width=True)

    # Descargar como Excel (sin la columna "Código ERSI Base")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.drop(columns=["Código ERSI Base"]).to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


