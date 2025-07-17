import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import io
import textwrap
import os

st.set_page_config(page_title="Generador de Código QR", page_icon="✅", layout="centered")

st.title("🔐 Generador de Código QR para usuarios semilla")
st.write("Complete la información y genere un código QR")

# === Formulario ===
# Detectar si viene desde ERSI
valor_por_defecto = st.session_state.get("ultimo_ersi", "")

# Formulario QR
with st.form("qr_form"):
    texto_qr = st.text_input("Código del usuario semilla (ERSI)", value=valor_por_defecto)
    texto_variable = st.text_input("Nombre de la clínica y contacto", "")

    generar = st.form_submit_button("Generar Código QR")


if generar and texto_qr and texto_variable:
    # Texto fijo
    texto_fijo = "Este cupón es valido en cuatro semanas después de su emisión. Debe presentarlo al acercarse a la clínica o lugar:"

    # Crear el código QR
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    ancho_qr, alto_qr = qr_img.size

    # Cargar fuentes DejaVuSans
    try:
        fuente_normal = ImageFont.truetype("DejaVuSans.ttf", 14)
        fuente_negrita = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except:
        fuente_normal = ImageFont.load_default()
        fuente_negrita = ImageFont.load_default()

    # Separar el texto en líneas según el ancho del QR
    max_chars_per_line = ancho_qr // 10  # ajustable según tamaño
    texto_fijo_lineas = textwrap.wrap(texto_fijo, width=max_chars_per_line)
    texto_variable_lineas = textwrap.wrap(texto_variable, width=max_chars_per_line)

    # Calcular altura total del texto
    num_lineas = len(texto_fijo_lineas) + len(texto_variable_lineas)
    altura_texto = 20 * num_lineas + 20
    alto_total = alto_qr + altura_texto

    # Crear imagen final (ajustando ancho si hace falta)
    ancho_total = ancho_qr
    imagen_final = Image.new("RGB", (ancho_total, alto_total), "white")
    imagen_final.paste(qr_img, ((ancho_total - ancho_qr) // 2, 0))
    draw = ImageDraw.Draw(imagen_final)

    # Dibujar texto fijo
    y_texto = alto_qr + 5
    for linea in texto_fijo_lineas:
        ancho_linea = draw.textlength(linea, font=fuente_normal)
        x_texto = (ancho_total - ancho_linea) // 2
        draw.text((x_texto, y_texto), linea, fill="black", font=fuente_normal)
        y_texto += 20

    # Dibujar texto variable en negrita
    for linea in texto_variable_lineas:
        ancho_linea = draw.textlength(linea, font=fuente_negrita)
        x_texto = (ancho_total - ancho_linea) // 2
        draw.text((x_texto, y_texto), linea, fill="black", font=fuente_negrita)
        y_texto += 20

    # Mostrar imagen
    st.image(imagen_final, caption="Código QR Generado", use_column_width=False)

    # Crear nombre del archivo basado en la clínica
    nombre_clinica = texto_variable.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"QR_{nombre_clinica}.png"

    # Descargar como PNG
    buffer = io.BytesIO()
    imagen_final.save(buffer, format="PNG")
    st.download_button(
        label="⬇️ Descargar QR como PNG",
        data=buffer.getvalue(),
        file_name=nombre_archivo,
        mime="image/png"
    )

elif generar:
    st.error("Por favor, complete ambos campos.")
