from __future__ import annotations

import pandas as pd
import streamlit as st
import auth as auth_backend

from app_ui import (
    APP_VERSION,
    footer,
    hero,
    inject_global_styles,
    notice,
    render_brand,
    render_sidebar,
    security_note,
    section,
    stats,
)
from auth import (
    auth_is_configured,
    create_managed_user,
    ensure_management_store,
    generate_secure_password,
    import_secret_users_to_managed,
    force_first_login_password_change_for_imported_users,
    list_audit_events,
    list_managed_users,
    list_secret_users,
    authenticate,
    change_own_password,
    current_user,
    get_security_settings,
    local_auth_is_configured,
    logout,
    oidc_auth_is_configured,
    set_managed_user_password,
    update_managed_user,
    require_auth,
    validate_password_strength,
    suggest_username,
 )


def change_password_with_current(username: str, current_password: str, new_password: str) -> tuple[bool, str]:
    """Compatibilidad V2.3.2 para cambio voluntario de contraseña.

    Usa el backend V2.3 cuando está disponible. Si Streamlit todavía carga
    un auth.py V2.2.x, aplica un fallback seguro con las funciones públicas
    que ya existían en esa versión. Esto evita que Home falle durante una
    actualización parcial del repositorio.
    """
    native = getattr(auth_backend, "change_password_with_current", None)
    if callable(native):
        return native(username, current_password, new_password)

    verify = getattr(auth_backend, "verify_password", None)
    if not callable(verify):
        return False, "El módulo de autenticación necesita actualizarse. Reemplace auth.py por la versión incluida con V2.3.2."

    normalized = str(username or "").strip().lower()
    try:
        records = list_managed_users()
    except Exception:
        return False, "No fue posible consultar la cuenta para validar la contraseña actual."

    user_record = next((u for u in records if str(u.get("username", "")).strip().lower() == normalized), None)
    if not user_record:
        return False, "La cuenta debe estar administrada desde el panel para cambiar la contraseña desde aquí."

    stored_hash = str(user_record.get("password_hash", ""))
    if not current_password:
        return False, "Ingrese su contraseña actual."
    if not verify(current_password, stored_hash):
        return False, "La contraseña actual no es correcta."
    if verify(new_password, stored_hash):
        return False, "La nueva contraseña debe ser diferente de la contraseña actual."

    return set_managed_user_password(
        normalized,
        new_password,
        updated_by=normalized,
        force_change=False,
    )


st.set_page_config(
    page_title="Plataforma ERSI | VIHCA",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_styles()


def cerrar_sesion() -> None:
    if st.session_state.get("registro") and not st.session_state.get("descargado", False):
        notice(
            "Antes de cerrar sesión, descargue la tabla con los códigos generados durante esta sesión.",
            "warning",
        )
        return
    logout()
    st.rerun()


def render_admin_panel(user: dict) -> None:
    """Renderiza la administración dentro de Home para evitar dependencias de rutas multipágina."""
    hero(
        "Administración segura",
        "Usuarios, permisos y bitácora",
        "Gestione el acceso a la plataforma sin editar código ni almacenar contraseñas en texto plano. Los cambios quedan registrados para trazabilidad.",
    )

    ok_store, store_message = ensure_management_store()
    if not ok_store:
        notice(store_message, "danger")
        security_note(
            "La administración usa el mismo Google Sheets y el mismo Service Account del generador ERSI. "
            "El mensaje anterior indica ahora la causa detectada; ya no se asume automáticamente que todo fallo sea un problema de permisos."
        )
        with st.expander("Comprobaciones rápidas"):
            st.markdown(
                """
                1. Confirme que el generador ERSI todavía puede guardar un código en la hoja principal.
                2. En Streamlit Secrets, conserve `google_sheets.spreadsheet_id` y `google_service_account`.
                3. El `client_email` del Service Account debe estar compartido como **Editor** en ese archivo.
                4. Si ya existen `USUARIOS_SISTEMA` o `AUDITORIA_SISTEMA`, no cambie manualmente sus encabezados.
                """
            )
        if st.button("Reintentar conexión administrativa", type="primary", width="stretch"):
            try:
                auth_backend._google_spreadsheet.clear()
            except Exception:
                pass
            st.rerun()
        footer("Administración")
        st.stop()

    managed_users = list_managed_users()
    secret_users = list_secret_users()
    active_count = sum(1 for u in managed_users if u.get("enabled"))
    admin_count = sum(1 for u in managed_users if u.get("role") == "admin" and u.get("enabled"))

    stats(
        [
            ("Usuarios administrados", str(len(managed_users))),
            ("Activos", str(active_count)),
            ("Administradores", str(admin_count)),
        ]
    )

    usuarios_tab, crear_tab, recuperar_tab, editar_tab, audit_tab = st.tabs(
        ["Usuarios", "Crear usuario", "Recuperar acceso", "Editar usuario", "Bitácora"]
    )

    with usuarios_tab:
        section(
            "Usuarios administrados desde la interfaz",
            "Estos usuarios se almacenan en USUARIOS_SISTEMA con contraseña protegida mediante hash PBKDF2-SHA256.",
        )

        if managed_users:
            df_users = pd.DataFrame(
                [
                    {
                        "Usuario": u["username"],
                        "Nombre": u["display_name"],
                        "País": u["pais"],
                        "Rol": {"admin": "Administrador", "coordinator": "Coordinador", "user": "Usuario"}.get(u["role"], u["role"]),
                        "Estado": "Activo" if u["enabled"] else "Inactivo",
                        "Cambio de contraseña": "Pendiente" if u["must_change_password"] else "No",
                        "Último acceso": u["last_login"] or "—",
                        "Creado por": u["created_by"] or "—",
                    }
                    for u in managed_users
                ]
            )
            st.dataframe(df_users, width="stretch", hide_index=True)
        else:
            notice("Todavía no hay usuarios administrados desde la interfaz.", "info")

        if admin_count < 2:
            notice(
                "Recomendación de recuperación: actualmente hay menos de dos administradores activos. Cree y verifique una cuenta de administrador de respaldo para evitar quedar sin acceso administrativo.",
                "warning",
            )
        else:
            notice(
                f"Recuperación administrativa preparada: hay {admin_count} administradores activos.",
                "success",
            )

        if secret_users:
            st.write("")
            section(
                "Migración de usuarios actuales",
                "Sus usuarios de Streamlit Secrets continúan funcionando. Puede copiarlos una sola vez a la gestión dinámica conservando sus hashes actuales.",
            )
            notice(
                "La migración no copia contraseñas en texto plano: únicamente traslada el hash existente. Los bloques de Secrets no se modifican automáticamente.",
                "info",
            )
            with st.expander(f"Ver usuarios detectados en Secrets ({len(secret_users)})"):
                df_secret = pd.DataFrame(
                    [
                        {
                            "Usuario": u["username"],
                            "Nombre": u["display_name"],
                            "País": u["pais"],
                            "Rol": u["role"],
                            "Estado": "Activo" if u["enabled"] else "Inactivo",
                        }
                        for u in secret_users
                    ]
                )
                st.dataframe(df_secret, width="stretch", hide_index=True)

            if st.button("Migrar usuarios de Secrets", type="primary"):
                imported, skipped, message = import_secret_users_to_managed(user["username"])
                if imported:
                    st.success(
                        f"{message} Importados: {imported}. Ya existentes/omitidos: {skipped}. "
                        "Los nuevos usuarios migrados deberán crear una contraseña personal en su primer ingreso."
                    )
                    st.rerun()
                else:
                    st.info(f"{message} No se agregaron usuarios nuevos; omitidos: {skipped}.")

            st.write("")
            notice(
                "Actualización de seguridad: si ya migró usuarios con una versión anterior, puede activar una sola vez el cambio obligatorio para esas cuentas. No cambia la contraseña temporal que ya les fue entregada.",
                "warning",
            )
            if st.button("Activar cambio de contraseña para usuarios migrados", width="stretch"):
                changed, skipped, message = force_first_login_password_change_for_imported_users(user["username"])
                if changed:
                    st.success(f"{message} Usuarios marcados: {changed}. Omitidos: {skipped}.")
                    st.rerun()
                else:
                    st.info(f"{message} Omitidos: {skipped}.")

            security_note(
                "Después de verificar que los usuarios migrados pueden ingresar y cambiar su contraseña, conviene dejar en Secrets únicamente una cuenta administrativa de recuperación."
            )

    with crear_tab:
        section(
            "Crear nuevo usuario",
            "Asigne el país y rol desde esta pantalla. La contraseña temporal se convierte en hash antes de guardarse.",
        )

        st.session_state.setdefault("admin_new_password_input", "")
        st.session_state.setdefault("admin_new_confirm_input", "")

        gen_col, hint_col = st.columns([1, 2.2])
        with gen_col:
            if st.button("Generar contraseña segura", width="stretch"):
                generated = generate_secure_password()
                st.session_state.admin_new_password_input = generated
                st.session_state.admin_new_confirm_input = generated
                st.rerun()
        with hint_col:
            st.caption("Puede generar una contraseña temporal o escribir una propia. Debe tener al menos 12 caracteres, mayúscula, minúscula, número y símbolo.")

        with st.form("create_user_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_display_name = st.text_input(
                    "Nombre completo / para mostrar*",
                    placeholder="Ej. Paola Argüello",
                    help="Este es el nombre que verá el equipo dentro de la plataforma. Puede contener espacios, mayúsculas y tildes.",
                )
                new_username = st.text_input(
                    "Usuario para iniciar sesión*",
                    placeholder="Ej. paola.arguello",
                    help="Puede escribir un usuario directamente o incluso un nombre completo; el sistema lo convertirá a un formato válido (minúsculas y sin espacios).",
                )
                st.caption("Ejemplo: Paola Argüello → paola.arguello. También se permiten punto, guion y guion bajo.")
                new_country = st.selectbox(
                    "País asignado*",
                    ["Honduras", "Guatemala", "El Salvador", "Nicaragua", "Panamá", "todos"],
                    format_func=lambda x: "Todos / Regional" if x == "todos" else x,
                )
            with c2:
                new_role = st.selectbox(
                    "Rol*",
                    ["user", "coordinator", "admin"],
                    format_func=lambda x: {"user": "Usuario", "coordinator": "Coordinador", "admin": "Administrador"}[x],
                )
                new_password = st.text_input(
                    "Contraseña temporal*",
                    type="password",
                    key="admin_new_password_input",
                )
                new_confirm = st.text_input(
                    "Confirmar contraseña*",
                    type="password",
                    key="admin_new_confirm_input",
                )

            enabled = st.checkbox("Usuario activo", value=True)
            force_change = st.checkbox("Solicitar cambio de contraseña en el próximo inicio", value=True)
            submit_new = st.form_submit_button("Crear usuario", type="primary", width="stretch")

        if submit_new:
            # Compatibilidad UX: si los campos fueron llenados al revés (nombre completo en usuario
            # y un identificador válido en nombre para mostrar), los intercambiamos automáticamente.
            effective_display_name = new_display_name.strip()
            effective_username_input = new_username.strip()
            display_as_username = suggest_username(effective_display_name)
            username_as_username = suggest_username(effective_username_input)
            if (
                " " in effective_username_input
                and effective_display_name
                and display_as_username == effective_display_name.lower()
                and 3 <= len(display_as_username) <= 40
            ):
                effective_display_name, effective_username_input = effective_username_input, effective_display_name

            normalized_username = suggest_username(effective_username_input or effective_display_name)

            if not effective_display_name:
                st.error("Ingrese el nombre completo o nombre para mostrar.")
            elif len(normalized_username) < 3:
                st.error("Ingrese un usuario de al menos 3 caracteres. También puede dejar un nombre completo para que el sistema lo normalice.")
            elif new_password != new_confirm:
                st.error("Las contraseñas no coinciden.")
            else:
                valid_password, password_message = validate_password_strength(new_password)
                if not valid_password:
                    st.error(password_message)
                else:
                    ok, message = create_managed_user(
                        username=normalized_username,
                        display_name=effective_display_name,
                        password=new_password,
                        pais=new_country,
                        role=new_role,
                        enabled=enabled,
                        created_by=user["username"],
                        must_change_password=force_change,
                    )
                    if ok:
                        st.session_state.last_created_username = normalized_username
                        st.session_state.last_created_password = new_password
                        st.success(f"{message} Usuario de acceso: {normalized_username}")
                    else:
                        st.error(message)

        if st.session_state.get("last_created_username") and st.session_state.get("last_created_password"):
            notice(
                "Credencial temporal creada. Entréguela al usuario por un canal seguro. Esta es la única pantalla donde conviene copiarla antes de generar otra.",
                "warning",
            )
            st.code(
                f"Usuario: {st.session_state.last_created_username}\nContraseña temporal: {st.session_state.last_created_password}",
                language="text",
            )
            if st.button("Ocultar credencial temporal creada"):
                st.session_state.pop("last_created_username", None)
                st.session_state.pop("last_created_password", None)
                st.rerun()

    with recuperar_tab:
        section(
            "Recuperar acceso de un usuario",
            "Si una persona olvidó su contraseña, genere una contraseña temporal. El sistema le exigirá crear una contraseña personal nueva en su siguiente ingreso.",
        )
        notice(
            "Por seguridad, la contraseña anterior no se puede consultar ni recuperar. El procedimiento correcto es restablecerla.",
            "info",
        )

        current_managed = list_managed_users()
        if not current_managed:
            notice("No hay usuarios administrados disponibles para restablecer.", "warning")
        else:
            by_username = {u["username"]: u for u in current_managed}
            recovery_usernames = list(by_username.keys())
            recovery_username = st.selectbox(
                "Usuario que necesita recuperar acceso",
                recovery_usernames,
                key="recovery_user_select",
                format_func=lambda x: f"{x} — {by_username[x].get('display_name') or x}",
            )
            recovery_user = by_username[recovery_username]

            # Evita reutilizar por accidente una contraseña temporal generada para
            # otro usuario si el administrador cambia la selección.
            if st.session_state.get("recovery_last_selected") != recovery_username:
                st.session_state.recovery_last_selected = recovery_username
                st.session_state.admin_recovery_password_input = ""
                st.session_state.admin_recovery_confirm_input = ""
                if st.session_state.get("last_reset_username") != recovery_username:
                    st.session_state.pop("last_reset_password", None)

            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("País", recovery_user.get("pais") or "—")
            with r2:
                st.metric("Rol", {"admin": "Administrador", "coordinator": "Coordinador", "user": "Usuario"}.get(recovery_user.get("role"), recovery_user.get("role", "—")))
            with r3:
                st.metric("Estado", "Activo" if recovery_user.get("enabled") else "Inactivo")

            if not recovery_user.get("enabled"):
                notice("Este usuario está inactivo. Puede restablecer la contraseña, pero deberá activarlo en 'Editar usuario' para permitir el ingreso.", "warning")
            if recovery_username.lower() == str(user.get("username", "")).lower():
                notice("Está seleccionando su propia cuenta. Para un cambio normal use 'Mi cuenta'. Utilice este restablecimiento solo si desea generar una contraseña temporal.", "warning")

            st.session_state.setdefault("admin_recovery_password_input", "")
            st.session_state.setdefault("admin_recovery_confirm_input", "")
            if st.button("Generar contraseña temporal segura", key="generate_recovery_password", width="stretch"):
                generated = generate_secure_password()
                st.session_state.admin_recovery_password_input = generated
                st.session_state.admin_recovery_confirm_input = generated
                st.rerun()

            with st.form("recovery_password_form"):
                reset_password = st.text_input(
                    "Contraseña temporal nueva*",
                    type="password",
                    key="admin_recovery_password_input",
                )
                reset_confirm = st.text_input(
                    "Confirmar contraseña temporal*",
                    type="password",
                    key="admin_recovery_confirm_input",
                )
                st.caption("El cambio de contraseña en el próximo inicio es obligatorio y no puede desactivarse en un restablecimiento.")
                reset_submit = st.form_submit_button("Restablecer acceso", type="primary", width="stretch")

            if reset_submit:
                if reset_password != reset_confirm:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, message = set_managed_user_password(
                        recovery_username,
                        reset_password,
                        updated_by=user["username"],
                        force_change=True,
                    )
                    if ok:
                        st.session_state.last_reset_username = recovery_username
                        st.session_state.last_reset_password = reset_password
                        st.success("Acceso restablecido. El usuario deberá cambiar esta contraseña temporal al ingresar.")
                    else:
                        st.error(message)

            if (
                st.session_state.get("last_reset_username") == recovery_username
                and st.session_state.get("last_reset_password")
            ):
                notice(
                    "Copie esta credencial temporal y entréguela únicamente a la persona correspondiente por un canal seguro. Después ocúltela de esta pantalla.",
                    "warning",
                )
                st.code(
                    f"Usuario: {recovery_username}\nContraseña temporal: {st.session_state.last_reset_password}",
                    language="text",
                )
                if st.button("Ocultar credencial temporal", key="hide_recovery_credential"):
                    st.session_state.pop("last_reset_username", None)
                    st.session_state.pop("last_reset_password", None)
                    st.session_state.admin_recovery_password_input = ""
                    st.session_state.admin_recovery_confirm_input = ""
                    st.rerun()

        st.write("")
        section(
            "Administrador de respaldo",
            "Mantenga una segunda cuenta administrativa verificada para recuperar la cuenta principal si el administrador habitual olvida su contraseña.",
        )
        current_managed = list_managed_users()
        active_admins = [
            u for u in current_managed
            if u.get("enabled") and str(u.get("role", "")).lower() == "admin"
        ]
        backup_user = next((u for u in current_managed if str(u.get("username", "")).lower() == "admin_respaldo"), None)

        if len(active_admins) >= 2:
            notice(f"La plataforma tiene {len(active_admins)} administradores activos. Ya existe redundancia para recuperación.", "success")
        else:
            notice("Solo hay un administrador activo. Si esa cuenta pierde acceso, será necesario intervenir manualmente en Google Sheets/Secrets.", "warning")

        if backup_user:
            status = "Activo" if backup_user.get("enabled") else "Inactivo"
            st.write(f"**Cuenta de respaldo:** `admin_respaldo` · **Estado:** {status}")
            st.caption("Si necesita renovar su contraseña, selecciónela arriba en 'Recuperar acceso'.")
            if not backup_user.get("enabled"):
                notice("La cuenta de respaldo existe pero está inactiva. Actívela desde 'Editar usuario' antes de depender de ella para emergencias.", "warning")
        else:
            notice(
                "Puede crear una cuenta `admin_respaldo`. Su contraseña temporal se mostrará una sola vez y deberá cambiarse al primer inicio.",
                "info",
            )
            if st.button("Crear administrador de respaldo", type="primary", key="create_backup_admin", width="stretch"):
                generated = generate_secure_password(18)
                ok, message = create_managed_user(
                    username="admin_respaldo",
                    display_name="Administrador de respaldo",
                    password=generated,
                    pais="todos",
                    role="admin",
                    enabled=True,
                    created_by=user["username"],
                    must_change_password=True,
                )
                if ok:
                    st.session_state.backup_admin_password = generated
                    st.success("Administrador de respaldo creado. Guarde la credencial temporal y pruebe la cuenta antes de considerarla lista.")
                else:
                    st.error(message)

        if st.session_state.get("backup_admin_password"):
            notice(
                "Credencial temporal de recuperación. No la envíe por correo grupal ni la almacene en el repositorio. Inicie sesión con `admin_respaldo` y establezca una contraseña personal antes de usarla como respaldo definitivo.",
                "warning",
            )
            st.code(
                f"Usuario: admin_respaldo\nContraseña temporal: {st.session_state.backup_admin_password}",
                language="text",
            )
            if st.button("Ocultar credencial de respaldo", key="hide_backup_admin_password"):
                st.session_state.pop("backup_admin_password", None)
                st.rerun()

        security_note(
            "La cuenta de respaldo no es una puerta trasera: es una segunda cuenta Administrador normal, auditada y protegida con las mismas reglas de contraseña, bloqueo e inactividad."
        )

    with editar_tab:
        section(
            "Editar usuario administrado",
            "Cambie nombre, país, rol o estado. Para conservar trazabilidad, los usuarios se desactivan en lugar de eliminarse.",
        )

        current_managed = list_managed_users()
        if not current_managed:
            notice("No hay usuarios administrados para editar. Cree uno o migre los usuarios de Secrets.", "info")
        else:
            by_username = {u["username"]: u for u in current_managed}
            selected_username = st.selectbox("Seleccione un usuario", list(by_username.keys()), key="edit_user_select")
            selected = by_username[selected_username]
            is_self = selected_username.lower() == str(user.get("username", "")).lower()

            if is_self:
                notice("Está editando su propia cuenta. No podrá desactivarla ni retirarse el rol Administrador desde esta sesión.", "warning")

            with st.form("edit_user_form"):
                e1, e2 = st.columns(2)
                with e1:
                    edit_name = st.text_input("Nombre para mostrar", value=selected["display_name"])
                    countries = ["Honduras", "Guatemala", "El Salvador", "Nicaragua", "Panamá", "todos"]
                    try:
                        country_index = countries.index(selected["pais"])
                    except ValueError:
                        country_index = len(countries) - 1
                    edit_country = st.selectbox(
                        "País asignado",
                        countries,
                        index=country_index,
                        format_func=lambda x: "Todos / Regional" if x == "todos" else x,
                    )
                with e2:
                    roles = ["user", "coordinator", "admin"]
                    try:
                        role_index = roles.index(selected["role"])
                    except ValueError:
                        role_index = 0
                    edit_role = st.selectbox(
                        "Rol",
                        roles,
                        index=role_index,
                        format_func=lambda x: {"user": "Usuario", "coordinator": "Coordinador", "admin": "Administrador"}[x],
                        disabled=is_self,
                    )
                    edit_enabled = st.checkbox("Usuario activo", value=selected["enabled"], disabled=is_self)
                    st.caption(f"Último acceso: {selected['last_login'] or 'Sin registro'}")

                save_edit = st.form_submit_button("Guardar cambios", type="primary", width="stretch")

            if save_edit:
                effective_role = selected["role"] if is_self else edit_role
                effective_enabled = True if is_self else edit_enabled
                ok, message = update_managed_user(
                    selected_username,
                    display_name=edit_name,
                    pais=edit_country,
                    role=effective_role,
                    enabled=effective_enabled,
                    updated_by=user["username"],
                )
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with audit_tab:
        section(
            "Bitácora de actividad",
            "Muestra los eventos más recientes de autenticación, administración y generación de códigos.",
        )
        events = list_audit_events(limit=300)
        if events:
            df_audit = pd.DataFrame(events).rename(
                columns={
                    "timestamp": "Fecha y hora",
                    "username": "Usuario",
                    "pais": "País",
                    "accion": "Acción",
                    "modulo": "Módulo",
                    "detalle": "Detalle",
                }
            )
            st.dataframe(df_audit, width="stretch", hide_index=True)
        else:
            notice("La bitácora todavía no contiene eventos.", "info")

    security_note("Las contraseñas reales nunca se almacenan en Google Sheets. Solo se conserva un hash no reversible con salt individual.")
    footer("Administración de usuarios")

def render_account_panel(user: dict) -> None:
    hero(
        "Seguridad de la cuenta",
        "Mi cuenta",
        "Cambie su contraseña personal cuando lo necesite. Para proteger la cuenta, el sistema solicita confirmar la contraseña actual.",
    )

    role_label = {"admin": "Administrador", "coordinator": "Coordinador", "user": "Usuario"}.get(
        str(user.get("role", "user")).lower(), str(user.get("role", "user"))
    )
    stats(
        [
            ("Usuario", user.get("username", "—")),
            ("País", user.get("pais", "—")),
            ("Rol", role_label),
        ]
    )

    if user.get("source") != "managed":
        notice(
            "Esta cuenta todavía se administra desde Streamlit Secrets u otro proveedor. El cambio de contraseña desde la plataforma está disponible para cuentas migradas a USUARIOS_SISTEMA.",
            "info",
        )
        footer("Mi cuenta")
        return

    section(
        "Cambiar mi contraseña",
        "Ingrese su contraseña actual y defina una nueva. La sesión permanecerá activa después del cambio.",
    )
    with st.form("voluntary_password_change"):
        current_password = st.text_input("Contraseña actual", type="password")
        new_password = st.text_input("Nueva contraseña", type="password")
        confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
        submit_change = st.form_submit_button("Actualizar contraseña", type="primary", width="stretch")

    if submit_change:
        if new_password != confirm_password:
            st.error("Las contraseñas nuevas no coinciden.")
        else:
            valid, message = validate_password_strength(new_password)
            if not valid:
                st.error(message)
            else:
                ok, message = change_password_with_current(
                    user["username"], current_password, new_password
                )
                if ok:
                    st.success("Contraseña actualizada correctamente. Utilice la nueva contraseña en su próximo ingreso.")
                else:
                    st.error(message)

    security_note(
        "La contraseña debe tener al menos 12 caracteres e incluir mayúscula, minúscula, número y símbolo. Nunca será visible para el administrador."
    )
    footer("Mi cuenta")


settings = get_security_settings()
user = current_user()

if not user:
    render_sidebar()
    col_logo, _ = st.columns([1.2, 2.8])
    with col_logo:
        render_brand()

    hero(
        "Proyecto VIHCA · Acceso protegido",
        "Plataforma ERSI y generación de códigos QR",
        "Gestione identificadores ERSI y materiales QR desde un entorno controlado, trazable y preparado para trabajo regional.",
    )

    if not auth_is_configured():
        notice("La autenticación segura todavía no está configurada.", "danger")
        notice(
            "Configure los usuarios en Streamlit Secrets. Después podrá migrarlos al panel de administración sin guardar contraseñas en el código.",
            "info",
        )
        security_note("Las contraseñas nunca deben escribirse directamente dentro de Home.py ni subirse al repositorio.")
        footer("Plataforma ERSI")
        st.stop()

    oidc_browser_logged_in = False
    try:
        oidc_browser_logged_in = bool(st.user.is_logged_in)
    except Exception:
        pass

    if oidc_browser_logged_in and settings.auth_mode in {"oidc", "both"}:
        notice("La cuenta autenticada no está autorizada para utilizar esta aplicación.", "danger")
        if st.button("Cerrar cuenta autenticada", width="stretch"):
            try:
                st.logout()
            except Exception:
                st.session_state.clear()
                st.rerun()
        footer("Plataforma ERSI")
        st.stop()

    if settings.auth_mode in {"oidc", "both"} and oidc_auth_is_configured():
        with st.container(border=True):
            st.markdown("### Acceso institucional")
            st.caption("Utilice la cuenta institucional autorizada por el administrador.")
            if st.button("Continuar con cuenta institucional", type="primary", width="stretch"):
                st.login()
        if settings.auth_mode == "both":
            st.markdown(
                "<div style='text-align:center;color:#526277;margin:10px 0'>o ingrese con credenciales locales autorizadas</div>",
                unsafe_allow_html=True,
            )

    if settings.auth_mode in {"local", "both"} and local_auth_is_configured():
        left, center, right = st.columns([1, 1.75, 1])
        with center:
            with st.container(border=True):
                st.markdown("### Inicio de sesión")
                st.caption("Ingrese sus credenciales autorizadas por Proyecto VIHCA.")
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                    password = st.text_input("Contraseña", type="password", placeholder="••••••••••••")
                    submitted = st.form_submit_button("Ingresar", type="primary", width="stretch")

                if submitted:
                    ok, message = authenticate(username, password)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                st.caption(
                    f"Protección activa: bloqueo por intentos fallidos · sesión expira tras "
                    f"{settings.session_timeout_minutes} min de inactividad."
                )

    security_note(
        "Las contraseñas locales se validan mediante PBKDF2-SHA256. El sistema también está preparado para autenticación institucional OIDC."
    )
    footer("Plataforma ERSI")
    st.stop()

user = require_auth(allow_password_change=True)
render_sidebar(user)

with st.sidebar:
    st.divider()
    is_admin = str(user.get("role", "user")).lower() == "admin"
    current_view = st.session_state.get("home_view", "home")

    if current_view != "home":
        if st.button("← Volver al inicio", width="stretch"):
            st.session_state.home_view = "home"
            st.rerun()
    else:
        if user.get("source") == "managed":
            if st.button("🔐 Mi cuenta", width="stretch"):
                st.session_state.home_view = "account"
                st.rerun()
        if is_admin:
            if st.button("⚙️ Administrar usuarios", width="stretch"):
                st.session_state.home_view = "admin"
                st.rerun()

    if st.button("Cerrar sesión", width="stretch"):
        cerrar_sesion()

# Un usuario creado desde el panel puede recibir una contraseña temporal.
if user.get("must_change_password") and user.get("source") == "managed":
    hero(
        "Seguridad de la cuenta",
        "Cambie su contraseña temporal",
        "Este es su primer acceso al sistema actualizado. Cree una contraseña personal antes de continuar; la contraseña temporal dejará de funcionar al guardar la nueva.",
    )
    with st.form("force_password_change"):
        new_password = st.text_input("Nueva contraseña", type="password")
        confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
        save_password = st.form_submit_button("Guardar nueva contraseña", type="primary", width="stretch")
    if save_password:
        valid, message = validate_password_strength(new_password)
        if not valid:
            st.error(message)
        elif new_password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        else:
            ok, message = change_own_password(user["username"], new_password)
            if ok:
                st.success("Contraseña actualizada. Ya puede utilizar la plataforma.")
                st.rerun()
            else:
                st.error(message)
    security_note("La nueva contraseña debe tener al menos 12 caracteres e incluir mayúscula, minúscula, número y símbolo. Debe ser diferente de la contraseña temporal.")
    footer("Plataforma ERSI")
    st.stop()

# Mi cuenta se renderiza en Home para evitar rutas adicionales.
if st.session_state.get("home_view") == "account":
    render_account_panel(user)
    st.stop()

# La administración se renderiza dentro de Home para no depender de una página registrada por Streamlit.
if st.session_state.get("home_view") == "admin":
    if str(user.get("role", "user")).lower() != "admin":
        st.session_state.home_view = "home"
        notice("Su cuenta no tiene permisos de administrador.", "danger")
    else:
        render_admin_panel(user)
        st.stop()

hero(
    "Centro operativo ERSI",
    f"Hola, {user.get('display_name') or user.get('username')}",
    "Gestione identificadores ERSI y genere tarjetas QR desde un mismo espacio. El último código creado permanece disponible durante la sesión para continuar el flujo sin volver a digitarlo.",
)

if st.session_state.get("registro") and not st.session_state.get("descargado", False):
    notice(
        "Hay códigos de esta sesión pendientes de descargar. Descargue la tabla antes de cerrar sesión para conservar su respaldo local.",
        "warning",
    )

col1, col2 = st.columns(2, gap="large")
with col1:
    with st.container(border=True):
        st.markdown(
            """
            <div class="vh-module-head">
              <div class="vh-module-icon">🧬</div>
              <div class="vh-module-title">Identificación ERSI</div>
              <div class="vh-module-copy">Genere el identificador único del voluntario y registre el evento de forma trazable.</div>
              <div class="vh-module-meta">País y servicio de salud · validaciones automáticas · registro centralizado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Crear código ERSI", type="primary", width="stretch"):
            st.switch_page("pages/1_Generador_Codigo_ERSI.py")

with col2:
    with st.container(border=True):
        st.markdown(
            """
            <div class="vh-module-head">
              <div class="vh-module-icon">▦</div>
              <div class="vh-module-title">Tarjeta QR</div>
              <div class="vh-module-copy">Convierta un código ERSI en una tarjeta QR clara y lista para entregar o compartir.</div>
              <div class="vh-module-meta">Código ERSI · clínica · contacto TBAC · archivo PNG</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Crear tarjeta QR", type="primary", width="stretch"):
            st.switch_page("pages/2_Generador_Codigo_QR.py")

if str(user.get("role", "user")).lower() == "admin":
    st.write("")
    with st.container(border=True):
        c_text, c_action = st.columns([2.4, 1])
        with c_text:
            st.markdown("### ⚙️ Administración del sistema")
            st.write("Cree y administre usuarios, asigne país y rol, restablezca contraseñas y consulte la bitácora de actividad.")
            st.caption("Disponible únicamente para cuentas con rol Administrador.")
        with c_action:
            st.write("")
            if st.button("Abrir administración", type="primary", width="stretch"):
                st.session_state.home_view = "admin"
                st.rerun()

st.markdown('<div class="vh-session-heading">Estado de la sesión</div>', unsafe_allow_html=True)
stats(
    [
        ("País asignado", user.get("pais", "—")),
        ("Códigos en sesión", str(len(st.session_state.get("registro", [])))),
        ("Versión", APP_VERSION),
    ]
)

security_note("No comparta credenciales ni deje la sesión abierta en equipos de uso compartido. Cierre sesión al finalizar.")
footer("Plataforma ERSI")
