# Corrección V2.3.1 — importación compatible

Esta versión corrige un fallo de arranque cuando `Home.py` V2.3.0 se despliega junto a un `auth.py` anterior.

## Archivos que deben reemplazarse juntos
- `Home.py`
- `auth.py`
- `app_ui.py`

V2.3.1 ya no depende de importar directamente `change_password_with_current` al iniciar la app. Si durante un despliegue parcial todavía se carga un `auth.py` V2.2.x, Home usa un fallback compatible en lugar de detener toda la aplicación.

Después del commit, use **Manage app → Reboot app** en Streamlit Cloud.
