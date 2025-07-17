import streamlit as st
import pandas as pd
import random
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ===
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope

)
client = gspread.authorize(creds)

# Parámetros de la hoja
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]

# === FUNCIONES ===
def generar_codigo_ersi(iniciales, fecha_nacimiento, sexo):
    fecha_str = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").strftime("%d%m%Y")
    base = f"{iniciales.upper()}{fecha_str}{sexo.upper()[0]}"
    worksheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    existing_data = pd.DataFrame(worksheet.get_all_records())

    # Evitar duplicados con sufijo incremental
    ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum() if not existing_data.empty else 0
    codigo_final = f"{base}-{ocurrencias + 1:03d}"
    return codigo_final

# === INTERFAZ STREAMLIT ===
st.set_page_config(page_title="Generador Código ERSI", layout="centered")
st.title("🔐 Generador de Código ERSI")

with st.form("ersi_form"):
    col1, col2 = st.columns(2)
    with col1:
        iniciales = st.text_input("Iniciales del nombre", max_chars=5)
        sexo = st.selectbox("Sexo", ["Femenino", "Masculino"])
    with col2:
        fecha_nac = st.date_input("Fecha de nacimiento", format="YYYY-MM-DD")
        edad = st.number_input("Edad", min_value=0, max_value=120, step=1)

    submitted = st.form_submit_button("Generar y Guardar")

if submitted:
    if iniciales and sexo and fecha_nac:
        fecha_nac_str = fecha_nac.strftime("%Y-%m-%d")
        codigo = generar_codigo_ersi(iniciales, fecha_nac_str, sexo)

        # Guardar en Google Sheets
        worksheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        worksheet.append_row([iniciales.upper(), fecha_nac_str, sexo, edad, codigo])

        st.success(f"Código ERSI generado: `{codigo}`")
    else:
        st.error("Por favor, complete todos los campos del formulario.")




