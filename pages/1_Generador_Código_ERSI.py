import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import io

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")

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

# === CARGAR DATOS DE CENTROS DE SALUD ===
data = pd.read_csv("https://raw.githubusercontent.com/cvalle2024/qr-generator/main/centros_salud_ersi.csv", encoding='latin1')
data.columns = data.columns.str.strip()

# === Inicializar almacenamiento ===
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === FORMULARIO ===
with st.form("ersi_formulario"):
    pais = st.selectbox("País", sorted(data['País'].dropna().unique()))
    departamentos = sorted(data[data['País'] == pais]['Departamento'].dropna().unique())
    departamento = st.selectbox("Departamento", departamentos)

    sitios = sorted(data[(data['País'] == pais) & (data['Departamento'] == departamento)]['Nombre del Sitio'].dropna().unique())
    servicio_salud = st.selectbox("Servicio de Salud", sitios)

    municipio = st.text_input("Municipio", "")

    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)

    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if all([pais, departamento, servicio_salud, municipio, iniciales, sexo, 15 <= edad <= 100]):
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"
        ocurrencias = sum(1 for reg in st.session_state["registro"] if base in reg["Código ERSI Base"])
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        nuevo = {
            "País": pais,
            "Departamento": departamento,
            "Municipio": municipio,
            "Servicio de Salud": servicio_salud,
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Base": codigo_base,
            "Código ERSI Único": codigo_base
        }

        st.session_state["registro"].append(nuevo)

        # Subir a Google Sheets (sin duplicados)
        hoja = sheet.get_all_records()
        existentes = [fila["Código ERSI Único"] for fila in hoja if "Código ERSI Único" in fila]
        if codigo_base not in existentes:
            sheet.append_row(list(nuevo.values()))

        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")
        st.session_state["ultimo_ersi"] = codigo_base

    else:
        st.error("Por favor, complete todos los campos correctamente.")

# Mostrar historial generado
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    # Descargar como Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.drop(columns=["Código ERSI Base"]).to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


