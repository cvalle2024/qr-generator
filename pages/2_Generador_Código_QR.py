import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import io
import textwrap

st.set_page_config(page_title="Generador de código QR para Reclutadores", page_icon="✅", layout="centered")

st.title("🔐 Generador de código QR para Reclutadores")
st.write("Complete la información y genere un código QR")

# === Detectar si viene desde ERSI ===
valor_por_defecto = st.session_state.get("ultimo_ersi", "")

# === Formulario ===
with st.form("qr_form"):
    texto_qr = st.text_input("Código único del Reclutador", value=valor_por_defecto)
    nombre_clinica = st.text_input("Nombre de la clínica o lugar", "")
    telefono = st.text_input("Por favor ingrese el número de teléfono", "")

    generar = st.form_submit_button("Generar Código QR")

# === Lógica ===
if generar and texto_qr and nombre_clinica:
    # Texto fijo
    texto_fijo = "Este cupón es válido por 4 semanas. Si ya venció, ¡aún te atenderán!    Preséntalo en la clínica o lugar:"

    # Construir texto variable combinando clínica y teléfono
    texto_variable = nombre_clinica
    if telefono.strip():
        texto_variable += f" | Tel: {telefono.strip()}"

    # Crear QR
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    ancho_qr, alto_qr = qr_img.size

    # Cargar fuente
    try:
        fuente_normal = ImageFont.truetype("DejaVuSans.ttf", 14)
        fuente_negrita = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except:
        fuente_normal = ImageFont.load_default()
        fuente_negrita = ImageFont.load_default()

    # Preparar líneas de texto
    max_chars_per_line = ancho_qr // 10
    texto_fijo_lineas = textwrap.wrap(texto_fijo, width=max_chars_per_line)
    texto_variable_lineas = textwrap.wrap(texto_variable, width=max_chars_per_line)

    num_lineas = len(texto_fijo_lineas) + len(texto_variable_lineas)
    altura_texto = 20 * num_lineas + 20
    alto_total = alto_qr + altura_texto

    # Imagen final
    imagen_final = Image.new("RGB", (ancho_qr, alto_total), "white")
    imagen_final.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(imagen_final)

    # Agregar texto fijo
    y_texto = alto_qr + 5
    for linea in texto_fijo_lineas:
        ancho_linea = draw.textlength(linea, font=fuente_normal)
        x_texto = (ancho_qr - ancho_linea) // 2
        draw.text((x_texto, y_texto), linea, fill="black", font=fuente_normal)
        y_texto += 20

    # Agregar texto variable (clínica y teléfono) en negrita
    for linea in texto_variable_lineas:
        ancho_linea = draw.textlength(linea, font=fuente_negrita)
        x_texto = (ancho_qr - ancho_linea) // 2
        draw.text((x_texto, y_texto), linea, fill="black", font=fuente_negrita)
        y_texto += 20

    # Mostrar en pantalla
    st.image(imagen_final, caption="Código QR Generado", use_column_width=False)

    # Nombre del archivo
    nombre_base = nombre_clinica.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"QR_{nombre_base}.png"

    # Descargar
    buffer = io.BytesIO()
    imagen_final.save(buffer, format="PNG")
    st.download_button(
        label="⬇️ Descargar QR como PNG",
        data=buffer.getvalue(),
        file_name=nombre_archivo,
        mime="image/png"
    )
