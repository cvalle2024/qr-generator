import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import io
import re

# === PREFIJOS POR PAÍS ===
prefijos_pais = {
    "Honduras": "+504",
    "Guatemala": "+502",
    "El Salvador": "+503",
    "Panamá": "+507",
    "Nicaragua": "+505"
}

# === Verificación de sesión ===
if "logueado" not in st.session_state or not st.session_state.logueado:
    st.warning("⚠️ Debe iniciar sesión para acceder.")
    st.stop()

# === Configuración de página ===
st.set_page_config(page_title="Generador de código QR para Voluntarios", page_icon="✅", layout="centered")
st.title("🔐 Generador de código QR para Voluntarios")
st.write("Complete la información y genere un código QR")

# === Detectar si viene desde ERSI ===
valor_por_defecto = st.session_state.get("ultimo_ersi", "")

# === Formulario ===
with st.form("qr_form"):
    texto_qr = st.text_input("Código único del Voluntario", value=valor_por_defecto)
    nombre_clinica = st.text_input("Nombre de la clínica o lugar", "")

    telefono_raw = st.text_input("☎️Número telefónico del TBAC (formato 9999-9999)", max_chars=9)
    telefono_limpio = re.sub(r"[^\d]", "", telefono_raw)

    if len(telefono_limpio) > 4:
        telefono_formateado = f"{telefono_limpio[:4]}-{telefono_limpio[4:8]}"
    else:
        telefono_formateado = telefono_limpio

    st.text_input("Teléfono formateado", value=telefono_formateado, disabled=True, label_visibility="collapsed")

    generar = st.form_submit_button("Generar código QR")

# === Lógica QR ===
if generar:
    errores = []

    if not texto_qr.strip():
        errores.append("❌ El campo de código del voluntario está vacío.")
    if not nombre_clinica.strip():
        errores.append("❌ El campo 'Nombre de la clínica o lugar' no puede estar vacío.")
    if not re.fullmatch(r"\d{4}-\d{4}", telefono_formateado):
        errores.append("❌ El número telefónico debe tener el formato correcto: 9999-9999.")

    if errores:
        for err in errores:
            st.error(err)
    else:
        # === Determinar prefijo del país ===
        pais_usuario = st.session_state.get("pais_usuario", "")
        prefijo = prefijos_pais.get(pais_usuario, "")

        # === Preparar textos
        texto_fijo_1 = "¡Hazlo por ti! Con este código puedes acercarte a : "
        texto_clinica = nombre_clinica.strip()
        texto_fijo_2 = "y acceder a una atención en salud, gratuita y 100% confidencial. "
        texto_telefono = f"Contáctanos al 📲:{prefijo} {telefono_formateado}" if telefono_formateado else ""
        texto_final = "Tu salud es tu poder. ¡Conócete, cuídate, vive!"

        # === Crear QR
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(texto_qr)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="darkblue", back_color="white").convert("RGB")
        ancho_qr, alto_qr = qr_img.size

        #Cragar la imagen
        logo_path="logo_vihca.jpg"
        logo=Image.open(logo_path)
        logo_size=int(qr_img.size[0] * 0.20)
        logo=logo_vihca.resize((logo_size,logo_size))

        pos= (
            (qr_img.size[0]-logo_size)//2,
            (qr_img.size[1]-logo_size)//2

        )

        # === Cargar fuentes
        try:
            fuente_normal = ImageFont.truetype("DejaVuSans.ttf", 16)
            fuente_clinica = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            fuente_telefono = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        except:
            fuente_normal = ImageFont.load_default()
            fuente_clinica = ImageFont.load_default()
            fuente_telefono = ImageFont.load_default()

        draw_temp = ImageDraw.Draw(qr_img)

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

        # === Preparar líneas
        lineas = []
        lineas += dividir_en_lineas(texto_fijo_1, fuente_normal, ancho_qr - 20)
        lineas += dividir_en_lineas(texto_clinica, fuente_clinica, ancho_qr - 20)
        lineas += dividir_en_lineas(texto_fijo_2, fuente_normal, ancho_qr - 20)
        if texto_telefono:
            lineas += dividir_en_lineas(texto_telefono, fuente_telefono, ancho_qr - 20)
        lineas += dividir_en_lineas(texto_final, fuente_normal, ancho_qr - 20)

        alto_texto = len(lineas) * (fuente_normal.size + 10) + 20
        alto_total = alto_qr + alto_texto

        imagen_final = Image.new("RGB", (ancho_qr, alto_total), "white")
        imagen_final.paste(qr_img, (0, 0))
        draw = ImageDraw.Draw(imagen_final)

        y = alto_qr + 10
        for linea, fuente in lineas:
            x = (ancho_qr - draw.textbbox((0, 0), linea, font=fuente)[2]) // 2
            draw.text((x, y), linea, font=fuente, fill="black")
            y += fuente.size + 10

        st.image(imagen_final, caption="Código QR generado", use_column_width=False)

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

# === Botón de volver al menú ===
st.markdown("Seleccione Menú:")
col1, = st.columns(1)
with col1:
    if st.button(" Regresar al menú"):
        st.switch_page("Home.py")
