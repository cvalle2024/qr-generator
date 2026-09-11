# Revisión técnica — Plataforma ERSI v2.0

Esta versión reemplaza la revisión v1.2.x e incorpora una renovación visual y de seguridad.

Validaciones realizadas antes de empaquetar:

- Compilación sintáctica de `Home.py`, `auth.py`, `app_ui.py`, ambas páginas y la herramienta de hashes.
- Validación TOML del ejemplo de Secrets.
- Prueba aislada de construcción de la tarjeta QR con Pillow/qrcode.
- Decodificación de la imagen QR de prueba: el contenido recuperado coincide exactamente con el código ERSI de entrada.
- Verificación criptográfica de que los hashes del paquete privado de migración corresponden a las nuevas contraseñas temporales generadas.

No se realizó una escritura real contra la hoja Google Sheets del usuario porque las credenciales de producción permanecen, correctamente, fuera del proyecto.

Consulte `CAMBIOS_V2.md` y `SEGURIDAD_Y_DESPLIEGUE.md`.
