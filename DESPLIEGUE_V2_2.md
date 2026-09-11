# Despliegue v2.2

1. Reemplace **todo el contenido del proyecto** por los archivos de este paquete. No mezcle páginas v1/v2.
2. Conserve los Secrets actuales de Google Sheets y autenticación.
3. Haga commit y espere el redeploy de Streamlit Cloud.
4. En `Manage app`, ejecute `Reboot app` una vez.
5. Ingrese con `admin_user`.
6. Abra **Administración del sistema**. La aplicación creará `USUARIOS_SISTEMA` y `AUDITORIA_SISTEMA` automáticamente.
7. En la pestaña Usuarios, use **Migrar usuarios de Secrets** para llevar los usuarios actuales a la interfaz.
8. Cierre sesión y compruebe el ingreso de al menos un usuario migrado.
9. Cuando haya comprobado la migración, puede dejar en Streamlit Secrets únicamente una cuenta administrativa de recuperación. Este paso es manual porque la aplicación no modifica Secrets.

## Importante

- Las contraseñas no se guardan en texto plano.
- `USUARIOS_SISTEMA` contiene hashes PBKDF2-SHA256.
- No comparta ni publique el Google Sheets de administración.
- Si desea aislar aún más la administración, configure opcionalmente `[user_management].spreadsheet_id` en Secrets y comparta ese spreadsheet solo con el Service Account.
