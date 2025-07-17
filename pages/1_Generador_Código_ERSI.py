import streamlit as st
import pandas as pd
import io
import json
from google.oauth2.service_account import Credentials
import gspread

# === CONFIGURACIÓN ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === AUTENTICACIÓN GOOGLE SHEETS ===
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    json.loads(st.secrets["google_sheets"]["gcp_service_account"]),
    scopes=SCOPE
)
client = gspread.authorize(creds)
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Leer datos actuales (si los hay)
data = sheet.get_all_records()
existing_data = pd.DataFrame(data) if data else pd.DataFrame(columns=["Iniciales", "Fecha de Nacimiento", "Sexo", "Edad", "Código ERSI Único"])

# === FORMULARIO ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)
    
    generar = st.form_submit_button("Generar Código ERSI")

# === LÓGICA DE GENERACIÓN ===
if generar:
    if iniciales and sexo and dia and mes:
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"

        # Verificar duplicados en la hoja
        if not existing_data.empty and "Código ERSI Único" in existing_data.columns:
            ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum()
        else:
            ocurrencias = 0

        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        nuevo_registro = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_base
        }

        # Agregar a la hoja
        sheet.append_row(list(nuevo_registro.values()))

        # Mostrar resultado
        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")

    else:
        st.error("Por favor, complete todos los campos correctamente.")

# === MOSTRAR REGISTROS EXISTENTES (OPCIONAL) ===
if not existing_data.empty:
    st.markdown("### 📋 Códigos ya generados")
    st.dataframe(existing_data, use_container_width=True)

    # Descargar como Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        existing_data.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




