# Cambios principales — ERSI v2.0

## Interfaz

- Nueva identidad visual unificada en `app_ui.py`.
- Fondo moderno, tarjetas, jerarquía tipográfica, paneles limpios y diseño adaptable a móvil.
- Inicio convertido en centro operativo con dos flujos claros: ERSI y QR.
- Barra lateral con identidad de usuario, país y estado de sesión.
- Indicadores rápidos de usuario, país y cantidad de registros de la sesión.
- Formularios reorganizados en bloques y columnas para reducir desplazamiento.
- Mensajes de éxito, advertencia y seguridad consistentes.

## Generador ERSI

- Catálogo de centros cacheado y depurado.
- País restringido según el usuario autenticado.
- Validación de día/mes (incluye febrero hasta 29 días).
- Normalización de iniciales y rechazo de caracteres no permitidos.
- Consulta del correlativo limitada a la columna del código en lugar de descargar toda la hoja.
- Google Sheets usa permisos mínimos de hoja de cálculo.
- Errores internos solo se registran en logs.
- Excel de sesión con autofiltro, fila superior congelada y anchos ajustados.
- Último país y servicio pasan automáticamente al generador QR.

## Generador QR

- Nueva tarjeta PNG de marca con logo VIHCA, código, QR y contenido de referencia.
- Mayor nivel de corrección QR (`ERROR_CORRECT_M`).
- QR de alto contraste y zona silenciosa conservada.
- Clínica y código se precargan desde el último ERSI.
- País/prefijo se hereda del registro; el administrador puede seleccionarlo.
- Validación de teléfono de 8 dígitos.
- Vista previa antes de descargar.
- Nombre de archivo saneado y limitado.

## Seguridad

Ver `SEGURIDAD_Y_DESPLIEGUE.md`.
