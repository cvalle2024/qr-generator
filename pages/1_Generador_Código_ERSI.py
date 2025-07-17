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
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# === FUNCIÓN PARA GENERAR CÓDIGO ERSI ===
def generar_codigo(iniciales, dia, mes, sexo, edad):
    base = f"{iniciales.upper()}{str(dia).zfill(2)}{str(mes).zfill(2)}{sexo[0].upper()}{str(edad).zfill(2)}"
    existing_data = pd.DataFrame(sheet.get_all_records())
    ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum() if "Código ERSI Único" in existing_data.columns else 0
    codigo = f"{base}-{ocurrencias+1:03d}"
    return codigo

# === TÍTULO ===
st.title("🧾 Generador de Código ERSI")

# === FORMULARIO ===
with st.form("form_ersi"):
    st.subheader("Ingrese los datos del usuario semilla")
    iniciales = st.text_input("Iniciales del nombre (ej. JP)", max_chars=4)
    col1, col2 = st.columns(2)
    with col1:
        dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    with col2:
        mes = st.number_input("Mes de nacimiento", min_value=1, max_value=12, step=1)
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad", min_value=0, max_value=120, step=1)
    
    submitted = st.form_submit_button("Generar Código ERSI")

    if submitted:
        if iniciales and dia and mes and sexo and edad:
            codigo = generar_codigo(iniciales, dia, mes, sexo, edad)
            sheet.append_row([iniciales, f"{str(dia).zfill(2)}/{str(mes).zfill(2)}", sexo, edad, codigo])
            st.success(f"✅ Código ERSI generado: `{codigo}`")
        else:
            st.warning("Por favor, complete todos los campos.")
