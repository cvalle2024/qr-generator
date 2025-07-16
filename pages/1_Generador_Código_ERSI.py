import streamlit as st
import pandas as pd
import io

st.session_state["ultimo_ersi"] = codigo_base
st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# Inicializar almacenamiento en sesión
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# === Formulario ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre (ej. LMOC)", "")
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1)
    mes = st.selectbox("Mes de nacimiento", ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])

    generar = st.form_submit_button("Generar Código ERSI")

if generar:
    if iniciales and sexo and dia and mes:
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"
        ocurrencias = sum(1 for reg in st.session_state["registro"] if base in reg["Código ERSI Base"])
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        # Guardar en memoria
        nuevo = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Código ERSI Base": codigo_base,
            "Código ERSI Único": codigo_base
        }
        st.session_state["registro"].append(nuevo)

        # Mostrar resultado
        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")
        st.session_state["ultimo_ersi"] = codigo_base  # Para pasar a QR si lo deseas

    else:
        st.error("Por favor, complete todos los campos.")

# Mostrar historial generado
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    # Descargar como Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
