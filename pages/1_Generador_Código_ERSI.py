import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Generador de Código ERSI", page_icon="🆔", layout="centered")

st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === Cargar sesión de usuarios guardados en memoria ===
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === Formulario ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre", "")
    fecha_nac = st.date_input("Fecha de Nacimiento")
    sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])

    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if iniciales and sexo and fecha_nac:
        # Formatear componentes
        dia = fecha_nac.day
        mes = fecha_nac.strftime("%b").upper()  # abreviado
        sexo_code = sexo[:2].upper()  # MA o FE

        # Generar código base
        base = f"{iniciales.upper()}{dia:02}{mes}{sexo_code}"

        # Contar cuántas veces ya existe ese código
        ocurrencias = sum(1 for reg in st.session_state["registro"] if base in reg["Código ERSI Base"])
        sufijo = f"-{ocurrencias + 1:03}"

        codigo_base = base + sufijo
        codigo_unico = codigo_base  # en esta versión el único = base

        # Guardar en memoria
        nuevo = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": fecha_nac.strftime("%d-%b-%Y"),
            "Sexo": sexo,
            "Código ERSI Base": codigo_base,
            "Código ERSI Único": codigo_unico
        }
        st.session_state["registro"].append(nuevo)

        st.success("✅ Código generado exitosamente")
        st.code(codigo_unico, language="text")

    else:
        st.error("Por favor, complete todos los campos.")

# === Mostrar tabla de códigos generados ===
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    # Botón para descargar
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="CodigosERSI")
       

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
