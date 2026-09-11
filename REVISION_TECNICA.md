# Revisión técnica — Generador ERSI / QR

Versión revisada para Streamlit 1.63.0 y Python 3.13. Se fija pandas 2.2.3 por estabilidad y compatibilidad con Python 3.13.

Cambios principales:

- `st.image(..., use_column_width=...)` reemplazado por `width="content"`.
- `st.dataframe(..., use_container_width=True)` reemplazado por `width="stretch"`.
- Validación de edad corregida para evitar `TypeError` cuando el valor es `None`.
- Ambas páginas internas exigen `logueado=True` y `verificado=True`.
- Acceso a Google Sheets protegido con manejo de errores y `st.cache_resource`.
- Si falla la lectura de Google Sheets, no se genera un nuevo correlativo.
- Si falla el guardado en Google Sheets, el registro no se agrega a la sesión.
- El correlativo ahora reconoce sufijos de más de 3 dígitos (`999`, `1000`, etc.).
- Se agregó un bloqueo compartido para reducir duplicados entre sesiones concurrentes del mismo proceso.
- Si se genera un registro después de descargar el Excel, `descargado` vuelve a `False`.
- Rutas de CSV y fuentes se resuelven desde la raíz del proyecto.
- Limpieza de `NaN` del catálogo para evitar opciones literales como `nan`.
- Dependencias fijadas en `requirements.txt` y se retiraron paquetes no usados (`oauth2client`, `chardet`).

## Recomendación de seguridad pendiente

Los usuarios y contraseñas continúan definidos en `Home.py` para no cambiar el mecanismo de acceso existente. Deben migrarse a `st.secrets` antes de publicar el repositorio de forma pública. El código de verificación mostrado en la misma pantalla no constituye un segundo factor real; sirve únicamente como paso adicional de confirmación.
