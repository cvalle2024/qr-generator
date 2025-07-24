import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import io
import streamlit as st

# Verificación de sesión: si no está logueado, redirigir al login
if "logueado" not in st.session_state or not st.session_state.logueado:
    st.warning("⚠️ Debe iniciar sesión para acceder.")
    st.stop()



st.set_page_config(page_title="Generador de código QR para Reclutadores", page_icon="✅", layout="centered")
st.title("🔐 Generador de código QR para Reclutadores")
st.write("Complete la información y genere un código QR")

# === Detectar si viene desde ERSI ===
valor_por_defecto = st.session_state.get("ultimo_ersi", "")

# === Formulario ===
with st.form("qr_form"):
    texto_qr = st.text_input("Código único del Reclutador", value=valor_por_defecto)
    nombre_clinica = st.text_input("Nombre de la clínica o lugar", "")
    telefono = st.text_input("Número telefónico del TBAC", "")

    generar = st.form_submit_button("Generar código QR")

# === Lógica QR ===
if generar and texto_qr and nombre_clinica:
    # === Preparar mensajes ===
    texto_fijo_1 = "¡Hazlo por ti! Con este código puedes acercarte a la clínica o lugar: "
    texto_clinica = nombre_clinica.strip()
    texto_fijo_2 = "y acceder a atención en salud, gratuita y 100% confidencial."
    texto_telefono = f"Contáctanos al : {telefono.strip()}" if telefono.strip() else ""
    texto_final = "Tu salud es tu poder. ¡Conócete, cuídate, vive!"

    # === Crear QR ===
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    ancho_qr, alto_qr = qr_img.size

    # === Cargar fuentes con tamaños diferenciados ===
    try:
        fuente_normal = ImageFont.truetype("DejaVuSans.ttf", 16)
        fuente_clinica = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        fuente_telefono = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except:
        fuente_normal = ImageFont.load_default()
        fuente_clinica = ImageFont.load_default()
        fuente_telefono = ImageFont.load_default()

    draw_temp = ImageDraw.Draw(qr_img)

    # === Función para dividir texto por líneas ajustado al ancho ===
    def dividir_en_lineas(texto, fuente, max_ancho):
        palabras = texto.split()
        lineas = []
        linea = ""
        for palabra in palabras:
            prueba = f"{linea} {palabra}".strip()
            if draw_temp.textbbox((0, 0), prueba, font=fuente)[2] <= max_ancho:
                linea = prueba
            else:
                lineas.append(linea)
                linea = palabra
        if linea:
            lineas.append(linea)
        return [(l, fuente) for l in lineas]

    # === Preparar líneas ===
    lineas = []
    lineas += dividir_en_lineas(texto_fijo_1, fuente_normal, ancho_qr - 20)
    lineas += dividir_en_lineas(texto_clinica, fuente_clinica, ancho_qr - 20)
    lineas += dividir_en_lineas(texto_fijo_2, fuente_normal, ancho_qr - 20)
    if texto_telefono:
        lineas += dividir_en_lineas(texto_telefono, fuente_telefono, ancho_qr - 20)
    lineas += dividir_en_lineas(texto_final, fuente_normal, ancho_qr - 20)

    # === Calcular alto total ===
    alto_texto = len(lineas) * (fuente_normal.size + 10) + 20
    alto_total = alto_qr + alto_texto

    # === Imagen final ===
    imagen_final = Image.new("RGB", (ancho_qr, alto_total), "white")
    imagen_final.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(imagen_final)

    # === Dibujar texto ===
    y = alto_qr + 10
    for linea, fuente in lineas:
        x = (ancho_qr - draw.textbbox((0, 0), linea, font=fuente)[2]) // 2
        draw.text((x, y), linea, font=fuente, fill="black")
        y += fuente.size + 10

    # === Mostrar imagen
    st.image(imagen_final, caption="Código QR generado", use_column_width=False)

    # === Descargar QR
    nombre_base = nombre_clinica.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"QR_{nombre_base}.png"
    buffer = io.BytesIO()
    imagen_final.save(buffer, format="PNG")
    st.download_button(
        label="⬇️ Descargar QR como PNG",
        data=buffer.getvalue(),
        file_name=nombre_archivo,
        mime="image/png"
    )

# Botón de volver al menú
st.markdown("Seleccione Menú:")
col1, = st.columns(1)
with col1:
    if st.button(" Regresar al menú"):
        st.switch_page("Home.py")
