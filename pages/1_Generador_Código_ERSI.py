import streamlit as st
import pandas as pd
import io
import os

ARCHIVO_CSV = "ersi_registros.csv"

# Leer el archivo persistente si existe
if os.path.exists(ARCHIVO_CSV):
    df_historial = pd.read_csv(ARCHIVO_CSV)
else:
    df_historial = pd.DataFrame(columns=["Iniciales", "Fecha de Nacimiento", "Sexo", "Edad", "Código ERSI Único"])

st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# === Formulario ===
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
        ocurrencias = sum(base in cod for cod in df_historial["Código ERSI Único"])
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        if codigo_base in df_historial["Código ERSI Único"].values:
            st.warning(f"⚠️ El código {codigo_base} ya fue registrado previamente.")
        else:
            nuevo = {
                "Iniciales": iniciales.upper(),
                "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
                "Sexo": sexo,
                "Edad": edad,
                "Código ERSI Único": codigo_base
            }
            df_historial = pd.concat([df_historial, pd.DataFrame([nuevo])], ignore_index=True)
            df_historial.to_csv(ARCHIVO_CSV, index=False)

            st.success("✅ Código generado exitosamente")
            st.code(codigo_base, language="text")
    else:
        st.error("Por favor, complete todos los campos correctamente.")

# Mostrar historial
if not df_historial.empty:
    st.markdown("### 📋 Códigos generados")
    st.dataframe(df_historial, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_historial.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


