import streamlit as st
import pandas as pd
import gspread
import json
import io
from google.oauth2.service_account import Credentials

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

# === CONFIGURACIÓN STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# Inicializar almacenamiento local
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === FORMULARIO ===
with st.form("ersi_formulario"):
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

        # Leer datos existentes desde Google Sheets
        try:
            existing_data = pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            st.error(f"No se pudo leer la hoja: {e}")
            existing_data = pd.DataFrame()

        # Verificar ocurrencias para evitar duplicados
        if not existing_data.empty and "Código ERSI Único" in existing_data.columns:
            ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum()
        else:
            ocurrencias = 0

        sufijo = f"-{ocurrencias + 1:03}"
        codigo_ersi = base + sufijo

        # Registrar en memoria local
        nuevo = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_ersi
        }
        st.session_state["registro"].append(nuevo)

        # Registrar en Google Sheets
        try:
            sheet.append_row(list(nuevo.values()))
            st.success("✅ Código generado y guardado exitosamente")
        except Exception as e:
            st.warning(f"Código generado, pero no se pudo guardar en Google Sheets: {e}")

        st.code(codigo_ersi, language="text")
        st.session_state["ultimo_ersi"] = codigo_ersi

    else:
        st.error("Por favor, complete todos los campos correctamente.")

# Mostrar historial generado
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados en esta sesión")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    # Descargar Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    )

