import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials
import json

# === CONFIGURACIÓN DE STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === CARGAR MAPEO DE UBICACIONES ===
data = pd.read_csv("https://raw.githubusercontent.com/cvalle/ersi-app/main/centros_salud_ersi.csv")


# === OBTENER LISTAS DE PAÍSES, DEPARTAMENTOS Y SERVICIOS ===
paises = sorted(data['País'].dropna().unique())

# === INICIALIZAR SESIÓN ===
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === FORMULARIO ===
with st.form("ersi_formulario"):
    pais = st.selectbox("País", paises)
    departamentos = sorted(data[data['País'] == pais]['DEPARTAMENTO'].dropna().unique())
    departamento = st.selectbox("Departamento", departamentos)
    municipios = sorted(data[(data['País'] == pais) & (data['DEPARTAMENTO'] == departamento)]['Municipio'].dropna().unique())
    municipio = st.selectbox("Municipio", municipios) if municipios else st.text_input("Municipio (ingrese manualmente)")
    servicios = sorted(data[(data['País'] == pais) & (data['DEPARTAMENTO'] == departamento) & (data['Municipio'] == municipio)]['Nombre del Sitio'].dropna().unique())
    servicio = st.selectbox("Servicio de Salud", servicios) if servicios else st.text_input("Servicio de Salud (manual)")

    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)

    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if all([pais, departamento, municipio, servicio, iniciales, sexo, dia, mes, (15 <= edad <= 100)]):
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
            "Servicio de Salud": servicio,
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Base": codigo_base,
            "Código ERSI Ùnico": codigo_base
        }

        st.session_state["registro"].append(nuevo)

        # === MOSTRAR RESULTADO ===
        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")

        # === GUARDAR EN GOOGLE SHEETS ===
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(
                st.secrets["google_service_account"],
                scopes=scope
            )
            client = gspread.authorize(creds)
            SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
            SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
            sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

            existing = sheet.col_values(10)  # Columna "Código ERSI Ùnico"
            if codigo_base not in existing:
                sheet.append_row(list(nuevo.values()))

        except Exception as e:
            st.error(f"Error al guardar en Google Sheets: {e}")
    else:
        st.error("Por favor, complete todos los campos correctamente.")

# === MOSTRAR HISTORIAL ===
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.drop(columns=["Código ERSI Base"]).to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

