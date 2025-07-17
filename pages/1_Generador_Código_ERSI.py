import streamlit as st
import pandas as pd
import io
import json
import gspread
from google.oauth2.service_account import Credentials

# === Configuración de la app ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === Autenticación con Google Sheets ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    json.loads(st.secrets["google_sheets"]["gcp_service_account"]),
    scopes=SCOPE
)
client = gspread.authorize(creds)

# === Datos de la hoja ===
SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# === Leer datos existentes ===
try:
    existing_data = pd.DataFrame(sheet.get_all_records())
except:
    existing_data = pd.DataFrame(columns=["Iniciales", "Fecha de Nacimiento", "Sexo", "Edad", "Código ERSI Único"])

# === Formulario de entrada ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun",
                                             "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)
    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if iniciales and sexo and dia and mes and (15 <= edad <= 100):
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"
        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"

        ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum()
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_final = base + sufijo

        nuevo_registro = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_final
        }

        # Agregar al registro remoto (Google Sheets)
        sheet.append_row(list(nuevo_registro.values()))

        # Mostrar resultado
        st.success("✅ Código generado exitosamente")
        st.code(codigo_final, language="text")

    else:
        st.error("Por favor, complete todos los campos correctamente.")




