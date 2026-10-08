# V2.3.3 — Optimización de Google Sheets (error 429)

Esta versión reduce las solicitudes realizadas por el panel de Administración a Google Sheets.

Cambios principales:
- Caché de 30 segundos para la lectura de USUARIOS_SISTEMA y AUDITORIA_SISTEMA.
- Invalidación automática de la caché después de crear, editar o restablecer un usuario.
- La validación de estructura de las hojas se ejecuta una vez por proceso y no en cada interacción.
- La preparación de hojas administrativas queda en caché y no se repite en cada rerun de Streamlit.
- Reintentos automáticos con espera progresiva cuando Google devuelve HTTP 429.
- Escrituras administrativas serializadas para reducir ráfagas concurrentes.
- La migración de usuarios desde Secrets utiliza append_rows para enviar varios registros en una sola solicitud.
- El botón Reintentar conexión limpia las cachés técnicas nuevas.

No cambia usuarios, contraseñas, Secrets ni la estructura de las hojas existentes.
