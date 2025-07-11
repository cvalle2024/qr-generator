import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import io

# === Configuración de la página ===
st.set_page_config(page_title="Generador QR - Ministerio de Salud", page_icon="✅", layout="centered")

st.title("🩺 Generador de Códigos QR para Clínicas")
st.write("Completa la información y genera el código QR con el texto estándar.")

# === Formulario de entrada ===
with st.form("qr_form"):
    texto_qr = st.text_input("Texto que contendrá el Código QR (dentro del QR)", "")
    texto_variable = st.text_input("Nombre de la Clínica (texto adicional debajo del QR)", "")

    generar = st.form_submit_button("Generar Código QR")

if generar and texto_qr and texto_variable:
    # Texto estandarizado
    texto_fijo = "Ministerio de Salud - Código de la Clínica:"
    texto_completo = f"{texto_fijo} {texto_variable}"

    # Generar QR
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Agregar texto debajo
    ancho_qr, alto_qr = qr_img.size
    fuente = ImageFont.load_default()

    # Ajustar texto en líneas si es necesario
    lineas = [texto_completo] if len(texto_completo) < 50 else [texto_completo[i:i+50] for i in range(0, len(texto_completo), 50)]
    alto_texto = 20 * len(lineas) + 10
    alto_total = alto_qr + alto_texto

    imagen_final = Image.new("RGB", (ancho_qr, alto_total), "white")
    imagen_final.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(imagen_final)
    y_texto = alto_qr + 5
    for linea in lineas:
        ancho_texto = draw.textlength(linea, font=fuente)
        x_texto = (ancho_qr - ancho_texto) // 2
        draw.text((x_texto, y_texto), linea, font=fuente, fill="black")
        y_texto += 20

    # Mostrar imagen
    st.image(imagen_final, caption="Código QR Generado", use_column_width=False)

    # Descargar como PNG
    buffer = io.BytesIO()
    imagen_final.save(buffer, format="PNG")
    st.download_button(
        label="⬇️ Descargar QR como PNG",
        data=buffer.getvalue(),
        file_name=f"QR_{texto_qr}.png",
        mime="image/png"
    )
elif generar:
    st.error("Por favor, completa ambos campos.")

