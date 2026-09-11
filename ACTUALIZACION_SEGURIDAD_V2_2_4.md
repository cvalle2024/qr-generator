# Plataforma ERSI v2.2.4 — cambio obligatorio de contraseña en primer acceso

## Objetivo
Los usuarios heredados del sistema anterior mantienen el mismo nombre de usuario y la contraseña temporal nueva generada durante la actualización de seguridad. Al primer acceso, deben crear una contraseña personal antes de poder ingresar a ERSI o QR.

## Flujo para usuarios existentes
1. Ingresan con su usuario habitual.
2. Utilizan la contraseña temporal nueva entregada por el administrador.
3. El sistema muestra `Cambie su contraseña temporal`.
4. Deben crear y confirmar una contraseña personal de al menos 12 caracteres, con mayúscula, minúscula, número y símbolo.
5. La nueva contraseña debe ser distinta de la temporal.
6. Al guardar, el hash de la contraseña temporal se reemplaza por el hash de la nueva contraseña y `must_change_password` pasa a `false`.
7. A partir de ese momento, solo funciona la nueva contraseña personal.

## Usuarios migrados anteriormente
Las versiones 2.2.x anteriores migraban usuarios con `must_change_password=false`. V2.2.4 incluye dos mecanismos de transición:

- En el primer inicio de sesión válido, una cuenta importada sin modificaciones posteriores se actualiza automáticamente para exigir el cambio.
- En Administración > Usuarios aparece el botón `Activar cambio de contraseña para usuarios migrados`, pensado para aplicar la actualización en bloque una sola vez a cuentas heredadas ya migradas. La ejecución queda registrada en `AUDITORIA_SISTEMA` para que no vuelva a forzar a usuarios que ya cambiaron su contraseña.

## Usuarios que se migren desde esta versión
Todo usuario importado desde Streamlit Secrets a partir de v2.2.4 se crea automáticamente con `must_change_password=true`.

## Protección de navegación
Mientras el cambio esté pendiente, el usuario no puede saltarse el proceso entrando directamente a las páginas ERSI o QR. Se le redirige a Home para establecer su contraseña personal.

## Despliegue
Reemplace `Home.py`, `auth.py` y `app_ui.py`, haga commit y luego reinicie la aplicación en Streamlit Cloud. No es necesario modificar los Secrets ni regenerar las contraseñas temporales existentes.
