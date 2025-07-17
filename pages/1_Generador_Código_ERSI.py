import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# === CONFIGURACIÓN ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1V1zrEYSj51BqRD9dkehjOHp2rglB3NwyIamTN4iPMCc/edit#gid=0"
CRED_FILE = "registrosersi-8b3f7cc1c416.json"

st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === CONECTAR A GOOGLE SHEETS ===
creds = ServiceAccountCredentials.from_json_keyfile_name(CRED_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1

# Leer datos existentes
datos_existentes = sheet.get_all_records()
df_existente = pd.DataFrame(datos_existentes)

# === FORMULARIO STREAMLIT ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)
    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if iniciales and dia and mes and sexo and edad:
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base_codigo = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"

        # Verificar cuántos ya existen con ese código base
        existentes_base = df_existente[df_existente["Código ERSI Único"].str.startswith(base_codigo)]
        sufijo = f"-{len(existentes_base) + 1:03}"

        codigo_unico = base_codigo + sufijo

        if codigo_unico in df_existente["Código ERSI Único"].values:
            st.warning("Este código ya fue generado antes. Se ha incrementado el sufijo automáticamente.")

        # Agregar nueva fila
        nueva_fila = [iniciales.upper(), f"{dia_str}-{mes_upper}", sexo, edad, codigo_unico]
        sheet.append_row(nueva_fila)

        st.success("✅ Código generado exitosamente")
        st.code(codigo_unico, language="text")
    else:
        st.error("Por favor complete todos los campos correctamente.")

# Mostrar tabla de códigos generados
st.markdown("### 📋 Códigos registrados")
if not df_existente.empty:
    st.dataframe(df_existente, use_container_width=True)
else:
    st.info("Aún no se han registrado códigos.")



