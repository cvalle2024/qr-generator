# Plataforma ERSI VIHCA v2.2

Aplicación Streamlit para generación y registro de códigos ERSI, creación de tarjetas QR y administración segura de usuarios.

## Módulos principales

- `Home.py`: acceso y centro operativo.
- `auth.py`: autenticación, bloqueo de intentos, sesión, usuarios administrados y auditoría.
- `app_ui.py`: identidad visual y contraste compartido.
- `pages/1_Generador_Codigo_ERSI.py`: generación y registro ERSI.
- `pages/2_Generador_Codigo_QR.py`: tarjeta QR y descarga PNG.
- `pages/3_Administracion_Usuarios.py`: alta, edición, activación, roles y restablecimiento de contraseñas.
- `DESPLIEGUE_V2_2.md`: pasos recomendados para actualizar desde v2.0/v2.1.
- `CAMBIOS_V2_2.md`: resumen técnico de mejoras.
- `.streamlit/secrets.example.toml`: estructura de Secrets sin credenciales reales.

## Administración de usuarios

Al abrir el módulo como administrador, la aplicación crea automáticamente:

- `USUARIOS_SISTEMA`
- `AUDITORIA_SISTEMA`

Las contraseñas no se almacenan en texto plano. El sistema conserva únicamente hashes PBKDF2-SHA256 con salt individual.

## Actualización

Para evitar mezclar páginas antiguas y nuevas, reemplace el proyecto completo con esta versión y luego ejecute `Reboot app` en Streamlit Cloud.
