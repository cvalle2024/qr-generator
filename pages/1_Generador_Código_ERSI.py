from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st
import io

# === CONFIGURACIÓN ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_ID = "1V1zrEYSj51BqRD9dkehjOHp2rglB3NwyIamTN4iPMCc"
SHEET_NAME = "Registros"

# === CONEXIÓN A GOOGLE SHEETS ===
creds = Credentials.from_service_account_file("/mnt/data/registrosersi-8b3f7cc1c416.json", scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# === CONFIGURACIÓN DE STREAMLIT ===
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === FORMULARIO ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre y Apellido (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad del usuario", min_value=15, max_value=100, step=1)
    generar = st.form_submit_button("Generar Código ERSI")

# === PROCESO DE GENERACIÓN ===
if generar:
    if iniciales and sexo and dia and mes:
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"
        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"

        # Leer códigos existentes
        try:
            existing_data = pd.DataFrame(sheet.get_all_records())
        except:
            existing_data = pd.DataFrame(columns=["Código ERSI Único"])

        ocurrencias = existing_data["Código ERSI Único"].str.contains(base, na=False).sum()
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_final = base + sufijo

        # Verificar duplicado
        if codigo_final in existing_data["Código ERSI Único"].values:
            st.error("⚠️ Este código ya ha sido generado previamente. Intente con otros datos.")
        else:
            # Guardar nuevo registro
            nuevo_registro = [iniciales.upper(), f"{dia_str}-{mes_upper}", sexo, edad, codigo_final]
            sheet.append_row(nuevo_registro)

            st.success("✅ Código generado exitosamente")
            st.code(codigo_final, language="text")

            # Mostrar tabla actualizada
            updated_data = pd.DataFrame(sheet.get_all_records())
            st.markdown("### 📋 Códigos generados")
            st.dataframe(updated_data, use_container_width=True)

            # Botón para descargar
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                updated_data.to_excel(writer, index=False, sheet_name="CodigosERSI")

            st.download_button(
                label="⬇️ Descargar Excel",
                data=buffer.getvalue(),
                file_name="codigos_ersi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("Por favor complete todos los campos correctamente.")





