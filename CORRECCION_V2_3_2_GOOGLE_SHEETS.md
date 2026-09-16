# Corrección V2.3.2 — Administración / Google Sheets

Esta versión corrige el diagnóstico genérico que mostraba todo fallo como si fuera un problema de permisos.

Cambios:
- La administración usa los mismos scopes de Google Sheets + Drive que el generador ERSI.
- Verifica primero el spreadsheet y la hoja principal configurada.
- Diferencia errores 403, 404, 400, configuración incompleta y estructura incompatible.
- Repara automáticamente una fila de encabezados parcial si no existen registros.
- Añade un botón para limpiar la conexión cacheada y reintentar.

No se modifican contraseñas ni usuarios existentes.
