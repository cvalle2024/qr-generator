# Plataforma ERSI VIHCA v2.0

Aplicación Streamlit para generación y registro de códigos ERSI y creación de tarjetas QR.

## Archivos principales

- `Home.py`: acceso y centro operativo.
- `auth.py`: autenticación, bloqueo de intentos y expiración de sesión.
- `app_ui.py`: identidad visual compartida.
- `pages/1_Generador_Codigo_ERSI.py`: generación y registro ERSI.
- `pages/2_Generador_Codigo_QR.py`: tarjeta QR y descarga PNG.
- `SEGURIDAD_Y_DESPLIEGUE.md`: pasos de configuración segura.
- `.streamlit/secrets.example.toml`: estructura de Secrets sin credenciales reales.

## Antes de desplegar

Lea primero `SEGURIDAD_Y_DESPLIEGUE.md`. La v2.0 no contiene contraseñas en el repositorio y requiere configurar usuarios en Streamlit Secrets o autenticación institucional OIDC.
