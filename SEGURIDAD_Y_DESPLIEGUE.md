# Plataforma ERSI v2.0 — Seguridad y despliegue

## Cambio obligatorio antes de publicar

La versión anterior contenía usuarios y contraseñas dentro de `Home.py`. En v2.0 esas credenciales **ya no existen en el código**.

Antes de publicar:

1. Cambie las contraseñas anteriores. Si el repositorio fue público, deben considerarse expuestas aunque se borren del archivo actual, porque pueden permanecer en el historial de Git.
2. Configure los usuarios en **Streamlit Community Cloud > App settings > Secrets**.
3. Mantenga allí también las secciones `google_sheets` y `google_service_account` que la aplicación ya utiliza.
4. Nunca suba `.streamlit/secrets.toml`, archivos con contraseñas, claves privadas o credenciales al repositorio.

`.gitignore` ya excluye `.streamlit/secrets.toml`.

## Autenticación local segura

En Secrets use:

```toml
[security]
auth_mode = "local"
max_attempts = 5
window_minutes = 15
lockout_minutes = 10
session_timeout_minutes = 30

[users."usuario_ejemplo"]
display_name = "Usuario Ejemplo"
pais = "Honduras"
role = "user"
enabled = true
password_hash = "pbkdf2_sha256$600000$..."
```

La aplicación no necesita conocer la contraseña original. Solo compara el hash PBKDF2 usando comparación de tiempo constante.

Para crear un hash nuevo:

```bash
python tools/generar_hash.py
```

Use contraseñas únicas de al menos 12 caracteres. No reutilice las contraseñas antiguas.

## OIDC institucional — opción recomendada a futuro

Streamlit 1.63 admite autenticación mediante OpenID Connect con proveedores como Google Identity, Microsoft Entra ID, Okta y otros compatibles.

Para habilitarla:

- Cambie `auth_mode` a `"oidc"` o `"both"`.
- Configure `[auth]` en Streamlit Secrets con el proveedor.
- Autorice explícitamente cada correo en `[oidc_users."correo@dominio.org"]` y asigne su país.
- El archivo `.streamlit/secrets.example.toml` incluye un ejemplo de estructura.

La aplicación incluye `streamlit[auth]` en `requirements.txt` para soportar esta opción.

## Protecciones incluidas en v2.0

- Contraseñas eliminadas del código fuente.
- Hash PBKDF2-SHA256 con salt individual y 600,000 iteraciones.
- Comparación segura con `hmac.compare_digest`.
- Respuesta uniforme para usuario inexistente o contraseña incorrecta.
- Bloqueo temporal después de intentos fallidos.
- Caducidad de sesión por inactividad.
- Acceso a páginas internas bloqueado sin sesión válida.
- Opción de OIDC institucional.
- Google Sheets usa únicamente el scope `spreadsheets`, reduciendo permisos innecesarios.
- Errores internos se envían al log del servidor sin mostrar detalles técnicos sensibles al usuario.
- Entradas de texto limitadas y saneadas antes de construir códigos y nombres de archivos.

## Observación sobre el correlativo ERSI

El bloqueo actual reduce el riesgo de duplicados entre sesiones que se ejecutan dentro del mismo proceso de Streamlit. Google Sheets no ofrece una transacción simple para `leer máximo + incrementar + guardar` desde este código. Si en el futuro existirán muchos usuarios generando códigos exactamente al mismo tiempo, conviene mover la asignación del correlativo a un backend transaccional (por ejemplo PostgreSQL) o a un servicio central con bloqueo atómico.

## Prueba mínima después del despliegue

1. Abrir la aplicación sin sesión e intentar entrar directamente a una URL de `pages/`: debe bloquear el acceso.
2. Probar contraseña incorrecta varias veces: debe activarse el bloqueo.
3. Iniciar sesión con un usuario de país y comprobar que solo vea ese país en ERSI.
4. Generar un ERSI y confirmar que el registro aparezca en Google Sheets.
5. Descargar el Excel de la sesión.
6. Abrir QR desde el último ERSI y confirmar código, clínica y prefijo telefónico.
7. Escanear el PNG con un teléfono.
8. Cerrar sesión y verificar que vuelva a solicitar autenticación.
