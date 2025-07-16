import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Generador de Código ERSI", layout="centered")
st.title("🧾 Generador de Código ERSI para usuarios semilla")
st.write("Complete el formulario para generar un código único por usuario.")

# Inicializar historial
if "registro" not in st.session_state:
    st.session_state["registro"] = []

# Claves para los widgets
clave_iniciales = "iniciales_input"
clave_dia = "dia_input"
clave_mes = "mes_input"
clave_sexo = "sexo_input"

# === Formulario ===
with st.form("ersi_formulario"):
    iniciales = st.text_input("Iniciales del Nombre (ej. LMOC)", key=clave_iniciales)
    dia = st.number_input("Día de nacimiento", min_value=1, max_value=31, step=1, key=clave_dia)
    mes = st.selectbox("Mes de nacimiento",
                       ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
                       key=clave_mes)
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=clave_sexo)

    generar = st.form_submit_button("Generar Código ERSI")

# === Procesar al enviar ===
if generar:
    if iniciales and sexo and dia and mes:
        dia_str = f"{int(dia):02}"
        mes_upper = mes.upper()
        sexo_code = "HO" if sexo == "Hombre" else "MU"

        base = f"{iniciales.upper()}{dia_str}{mes_upper}{sexo_code}"
        ocurrencias = sum(1 for reg in st.session_state["registro"] if base in reg["Código ERSI Base"])
        sufijo = f"-{ocurrencias + 1:03}"
        codigo_base = base + sufijo

        nuevo = {
            "Iniciales": iniciales.upper(),
            "Fecha de Nacimiento": f"{dia_str}-{mes_upper}",
            "Sexo": sexo,
            "Código ERSI Base": codigo_base,
            "Código ERSI Único": codigo_base
        }
        st.session_state["registro"].append(nuevo)

        st.success("✅ Código generado exitosamente")
        st.code(codigo_base, language="text")

        # Guardar en sesión para QR
        st.session_state["ultimo_ersi"] = codigo_base

    else:
        st.error("Por favor, complete todos los campos.")

# === Mostrar historial ===
if st.session_state["registro"]:
    st.markdown("### 📋 Códigos generados")
    df = pd.DataFrame(st.session_state["registro"])
    st.dataframe(df, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="CodigosERSI")

    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="codigos_ersi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


