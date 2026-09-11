# Plataforma ERSI v2.2.0

## Cambios principales

- Contraste corregido para títulos, botones, alertas, inputs y textos aunque el navegador estuviera usando tema oscuro.
- Ambos botones del Home usan estilo primario visible y consistente.
- El estado de sesión usa tarjetas propias de la interfaz en lugar de métricas nativas con poco contraste.
- Generador QR totalmente sincronizado con el diseño v2.2 y con un solo campo de teléfono.
- Tarjeta QR institucional renovada y lista para PNG.
- Nuevo módulo **Administración de usuarios** exclusivo para rol `admin`.
- Usuarios dinámicos almacenados en la hoja `USUARIOS_SISTEMA` usando únicamente hashes PBKDF2-SHA256.
- Hoja `AUDITORIA_SISTEMA` para trazabilidad de accesos, administración, ERSI y QR.
- Creación de usuarios, país, rol, activar/desactivar y restablecer contraseña desde interfaz.
- Opción para migrar una sola vez los usuarios actuales de Streamlit Secrets a la gestión dinámica.
- Contraseña temporal con cambio obligatorio en el siguiente inicio de sesión.
- Se conserva compatibilidad con las variables antiguas `logueado` y `verificado` durante la transición.

## Roles

- `admin`: acceso a todos los módulos y administración de usuarios.
- `coordinator`: acceso operativo; preparado para permisos ampliados por país.
- `user`: acceso operativo a ERSI y QR.

## Hojas creadas automáticamente

Al entrar por primera vez a Administración, el sistema crea en el Google Sheets configurado:

- `USUARIOS_SISTEMA`
- `AUDITORIA_SISTEMA`

No se debe crear manualmente su estructura.
