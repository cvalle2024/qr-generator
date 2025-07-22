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
df_centros["Departamento"] = df_centros["Departamento"].astype(str).str.strip().str.title()
df_centros["Nombre del Sitio"] = df_centros["Nombre del Sitio"].astype(str).str.strip().str.title()

# === CONFIGURACIÓN DE STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("Generador de código único para Reclutadores")
st.write("Complete el formulario para generar un código único por Reclutadores.")

if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === SELECCIÓN DE UBICACIÓN ===
st.markdown("### Selección de Ubicación")

paises_disponibles = sorted(df_centros["País"].dropna().unique())
pais_seleccionado = st.selectbox("País", paises_disponibles)

df_filtrado_pais = df_centros[df_centros["País"] == pais_seleccionado]

departamentos_disponibles = sorted(df_filtrado_pais["Departamento"].dropna().unique())
departamento_seleccionado = st.selectbox("Departamento", departamentos_disponibles)

df_filtrado_depto = df_filtrado_pais[df_filtrado_pais["Departamento"] == departamento_seleccionado]
sitios_disponibles = sorted(df_filtrado_depto["Nombre del Sitio"].dropna().unique())
servicio_salud = st.selectbox("Servicio de Salud", sitios_disponibles)

# === FORMULARIO PARA DATOS PERSONALES ===
with st.form("ersi_formulario"):
    st.markdown("### 👤 Información del Reclutador")
    iniciales = st.text_input("Ingrese las primeras 2 letras de un nombre y de un apellido (máx. 4 letras, ej. CABU)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del Reclutador", min_value=15, max_value=100, step=1)
    generar = st.form_submit_button("Generar código único del Reclutador")

# === LÓGICA DE GENERACIÓN DE CÓDIGO ===
if generar:
    campos_llenos = all([
        pais_seleccionado,
        departamento_seleccionado,
        servicio_salud,
        iniciales.strip(),
        sexo,
        dia,
        mes,
        15 <= edad <= 100
    ])

    if not campos_llenos:
        st.error("❌ Por favor, complete todos los campos obligatorios antes de generar el código.")
    elif len(iniciales.strip()) < 4:
        st.error("❌ Las iniciales deben tener máximo 4 letras.")
    else:
        # === CONSTRUCCIÓN DEL CÓDIGO ===
        pais_code = pais_seleccionado[:3].upper()
        iniciales_code = iniciales.strip().upper()
        dia_str = f"{int(dia):02}"
        mes_code = mes.upper()
        sexo_code = "H" if sexo == "Hombre" else "M"

        base = f"{pais_code}-{iniciales_code}{dia_str}{mes_code}-{sexo_code}"

        # === CÁLCULO DE SUFIJO ÚNICO ===
        try:
            existing_data = pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            st.error(f"No se pudo leer la hoja: {e}")
            existing_data = pd.DataFrame()

        if not existing_data.empty and "Código ERSI Único" in existing_data.columns:
            ocurrencias = existing_data["Código ERSI Único"].str.startswith(base).sum()
        else:
            ocurrencias = 0

        sufijo = f"{ocurrencias + 1:03}"
        codigo_ersi = f"{base}-{sufijo}"

        nuevo = {
            "País": pais_seleccionado,
            "Departamento": departamento_seleccionado,
            "Servicio de Salud": servicio_salud,
            "Iniciales": iniciales_code,
            "Fecha de Nacimiento": f"{dia_str}-{mes_code}",
            "Sexo": sexo,
            "Edad": edad,
            "Código ERSI Único": codigo_ersi
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
                nuevo["Código ERSI Único"]
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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
