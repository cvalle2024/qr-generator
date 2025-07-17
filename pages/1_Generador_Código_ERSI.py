import streamlit as st
import pandas as pd
import gspread
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

# === CARGA DE DATOS DE CENTROS DE SALUD ===
df_centros = pd.read_csv("centros_salud_ersi.csv", encoding="latin-1")
df_centros["País"] = df_centros["País"].astype(str).str.strip()
df_centros["Departamento"] = df_centros["Departamento"].astype(str).str.strip()
df_centros["Nombre del Sitio"] = df_centros["Nombre del Sitio"].astype(str).str.strip()
paises = sorted(df_centros["País"].dropna().unique())

# === CONFIGURACIÓN DE STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("📟 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === MEMORIA LOCAL DE STREAMLIT ===
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === FORMULARIO DE ENTRADA ===
with st.form("ersi_formulario"):
    pais_mostrado = st.selectbox("País", paises)
    df_filtrado_pais = df_centros[df_centros["País"] == pais_mostrado]

    departamentos = sorted(df_filtrado_pais["Departamento"].dropna().unique())
    departamento = st.selectbox("Departamento", departamentos)

    sitios_filtrados = df_filtrado_pais[df_filtrado_pais["Departamento"] == departamento]["Nombre del Sitio"].dropna().unique()
    servicio_salud = st.selectbox("Servicio de Salud", sorted(sitios_filtrados))

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

        try:
            existing_data = pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            st.error(f"No se pudo leer la hoja: {e}")
            existing_data = pd.DataFrame()

        if not existing_data.empty and "Código ERSI Único" in existing_data.columns:
            ocurrencias = existing_data["Código ERSI Único"].str.startswith(base).sum()
        else:
            ocurrencias = 0

        sufijo = f"-{ocurrencias + 1:03}"
        codigo_ersi = base + sufijo

        nuevo = {
            "País": pais_mostrado,
            "Departamento": departamento,
            "Servicio de Salud": servicio_salud,
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_ersi
        }
        st.session_state["registro"].append(nuevo)

        try:
            sheet.append_row(list(nuevo.values()))
            st.success("✅ Código generado y guardado exitosamente")
        except Exception as e:
            st.warning(f"Código generado, pero no se pudo guardar en Google Sheets: {e}")

        st.code(codigo_ersi, language="text")
        st.session_state["ultimo_ersi"] = codigo_ersi
    else:
        st.error("Por favor, complete todos los campos correctamente.")

# === TABLA Y DESCARGA ===
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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


