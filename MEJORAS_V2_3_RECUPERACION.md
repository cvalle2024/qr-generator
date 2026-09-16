# Plataforma ERSI v2.3.0 — Recuperación de acceso

## Cambios principales

- Nueva pestaña **Recuperar acceso** para administradores.
- El administrador puede generar una contraseña temporal para cualquier usuario administrado.
- Todo restablecimiento obliga al usuario a crear una contraseña personal en el siguiente inicio.
- La contraseña anterior nunca se muestra ni puede recuperarse; solo se reemplaza.
- Nueva opción **Mi cuenta** para que cada usuario administrado cambie voluntariamente su contraseña confirmando primero la actual.
- Nueva opción para crear `admin_respaldo`, una segunda cuenta administradora destinada a recuperación.
- Protección backend para impedir que se desactive o degrade al último administrador activo.
- Todos los cambios de contraseña y acciones administrativas continúan registrándose en la bitácora.

## Recomendación al desplegar

1. Reemplace el proyecto por esta versión y reinicie la app.
2. Ingrese con el administrador principal.
3. Abra **Administración > Recuperar acceso**.
4. Cree `admin_respaldo`.
5. Copie su contraseña temporal por un canal seguro.
6. Cierre sesión, pruebe `admin_respaldo` y establezca su contraseña personal.
7. Guarde la contraseña del respaldo en un gestor de contraseñas institucional.

No coloque contraseñas dentro del repositorio ni en archivos compartidos.
