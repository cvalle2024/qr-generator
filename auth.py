from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import logging
import re
import secrets as pysecrets
import string
import threading
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

DEFAULT_ITERATIONS = 600_000
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_WINDOW_MINUTES = 15
DEFAULT_LOCKOUT_MINUTES = 10
DEFAULT_SESSION_TIMEOUT_MINUTES = 30

MANAGED_USERS_SHEET = "USUARIOS_SISTEMA"
AUDIT_SHEET = "AUDITORIA_SISTEMA"
MANAGED_USER_HEADERS = [
    "username",
    "display_name",
    "password_hash",
    "pais",
    "role",
    "enabled",
    "must_change_password",
    "created_at",
    "created_by",
    "updated_at",
    "last_login",
]
AUDIT_HEADERS = ["timestamp", "username", "pais", "accion", "modulo", "detalle"]


@dataclass(frozen=True)
class SecuritySettings:
    auth_mode: str = "local"
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    window_minutes: int = DEFAULT_WINDOW_MINUTES
    lockout_minutes: int = DEFAULT_LOCKOUT_MINUTES
    session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES


@st.cache_resource
def _attempt_store():
    return {
        "lock": threading.Lock(),
        "attempts": defaultdict(deque),
        "locked_until": {},
    }


@st.cache_resource
def _google_spreadsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["google_service_account"]),
        scopes=scope,
    )
    client = gspread.authorize(creds)
    # Se permite separar la administración de usuarios en otro spreadsheet si se desea.
    try:
        user_mgmt = st.secrets.get("user_management", {})
        sheet_id = str(user_mgmt.get("spreadsheet_id", "")).strip()
    except Exception:
        sheet_id = ""
    if not sheet_id:
        sheet_id = str(st.secrets["google_sheets"]["spreadsheet_id"]).strip()
    return client.open_by_key(sheet_id)


def _secret_section(name: str):
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return None


def get_security_settings() -> SecuritySettings:
    section = _secret_section("security")
    if not section:
        return SecuritySettings()

    def safe_int(key: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(section.get(key, default))
        except (TypeError, ValueError):
            return default
        return min(max(value, minimum), maximum)

    auth_mode = str(section.get("auth_mode", "local")).strip().lower()
    if auth_mode not in {"local", "oidc", "both"}:
        auth_mode = "local"

    return SecuritySettings(
        auth_mode=auth_mode,
        max_attempts=safe_int("max_attempts", DEFAULT_MAX_ATTEMPTS, 3, 20),
        window_minutes=safe_int("window_minutes", DEFAULT_WINDOW_MINUTES, 1, 120),
        lockout_minutes=safe_int("lockout_minutes", DEFAULT_LOCKOUT_MINUTES, 1, 240),
        session_timeout_minutes=safe_int("session_timeout_minutes", DEFAULT_SESSION_TIMEOUT_MINUTES, 5, 480),
    )


def _users_section():
    section = _secret_section("users")
    return section or {}


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    salt = pysecrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(calculated, expected)
    except (ValueError, TypeError, binascii.Error):
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Incluya al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "Incluya al menos una letra minúscula."
    if not re.search(r"\d", password):
        return False, "Incluya al menos un número."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Incluya al menos un símbolo."
    return True, "Contraseña válida."


def generate_secure_password(length: int = 16) -> str:
    length = max(14, min(int(length), 32))
    symbols = "!@#$%*-_+"
    required = [
        pysecrets.choice(string.ascii_uppercase),
        pysecrets.choice(string.ascii_lowercase),
        pysecrets.choice(string.digits),
        pysecrets.choice(symbols),
    ]
    pool = string.ascii_letters + string.digits + symbols
    chars = required + [pysecrets.choice(pool) for _ in range(length - len(required))]
    pysecrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _normalize_username(username: str) -> str:
    return str(username or "").strip().lower()


def suggest_username(value: str) -> str:
    """Convierte un nombre o texto libre en un usuario seguro y legible.

    Ejemplo: ``Paola Argüello`` -> ``paola.arguello``.
    Conserva puntos, guiones y guiones bajos válidos.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", ".", normalized)
    normalized = re.sub(r"[^a-z0-9._-]", "", normalized)
    normalized = re.sub(r"\.{2,}", ".", normalized)
    normalized = normalized.strip("._-")
    return normalized[:40]


def _normalize_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "si", "sí", "activo"}:
        return True
    if text in {"false", "0", "no", "inactivo"}:
        return False
    return default


def _secret_user(username: str) -> dict | None:
    target = _normalize_username(username)
    for key, raw in _users_section().items():
        if _normalize_username(str(key)) != target:
            continue
        data = dict(raw)
        data["username"] = str(key)
        data.setdefault("display_name", str(key))
        data.setdefault("pais", "")
        data.setdefault("enabled", True)
        data.setdefault("role", "user")
        data["source"] = "secrets"
        data["must_change_password"] = False
        return data
    return None


def _worksheet(title: str, create: bool = False, headers: list[str] | None = None):
    try:
        book = _google_spreadsheet()
        try:
            ws = book.worksheet(title)
        except gspread.WorksheetNotFound:
            if not create:
                return None
            ws = book.add_worksheet(title=title, rows=500, cols=max(12, len(headers or [])))
            if headers:
                ws.append_row(headers, value_input_option="RAW")
            return ws

        if headers:
            values = ws.row_values(1)
            if not values:
                ws.append_row(headers, value_input_option="RAW")
            elif [str(v).strip() for v in values[: len(headers)]] != headers:
                # No sobrescribe estructuras desconocidas. Fuerza una falla legible para no corromper datos.
                raise ValueError(f"La hoja {title} existe pero no tiene la estructura esperada.")
        return ws
    except Exception:
        logger.exception("No fue posible abrir la hoja de gestión %s", title)
        if create:
            raise
        return None


def ensure_management_store() -> tuple[bool, str]:
    try:
        _worksheet(MANAGED_USERS_SHEET, create=True, headers=MANAGED_USER_HEADERS)
        _worksheet(AUDIT_SHEET, create=True, headers=AUDIT_HEADERS)
        return True, "Las hojas de administración están listas."
    except Exception:
        return False, "No fue posible preparar las hojas de administración. Revise permisos del Service Account."


def _rows_as_dicts(ws, headers: list[str]) -> list[dict]:
    values = ws.get_all_values()
    if not values:
        return []
    actual_headers = [str(v).strip() for v in values[0]]
    if actual_headers[: len(headers)] != headers:
        raise ValueError("La hoja no tiene la estructura esperada.")
    rows: list[dict] = []
    for idx, raw in enumerate(values[1:], start=2):
        padded = list(raw) + [""] * max(0, len(headers) - len(raw))
        record = {headers[i]: padded[i] for i in range(len(headers))}
        record["_row_index"] = idx
        rows.append(record)
    return rows


def _managed_user(username: str) -> dict | None:
    target = _normalize_username(username)
    if not target:
        return None
    ws = _worksheet(MANAGED_USERS_SHEET, create=False, headers=MANAGED_USER_HEADERS)
    if ws is None:
        return None
    try:
        for row in _rows_as_dicts(ws, MANAGED_USER_HEADERS):
            if _normalize_username(row.get("username", "")) != target:
                continue
            return {
                **row,
                "username": str(row.get("username", "")).strip(),
                "display_name": str(row.get("display_name", "")).strip() or target,
                "pais": str(row.get("pais", "")).strip(),
                "role": str(row.get("role", "user")).strip().lower() or "user",
                "enabled": _normalize_bool(row.get("enabled"), True),
                "must_change_password": _normalize_bool(row.get("must_change_password"), False),
                "source": "managed",
            }
    except Exception:
        logger.exception("No fue posible consultar usuarios administrados")
    return None


def list_managed_users() -> list[dict]:
    ws = _worksheet(MANAGED_USERS_SHEET, create=False, headers=MANAGED_USER_HEADERS)
    if ws is None:
        return []
    rows = _rows_as_dicts(ws, MANAGED_USER_HEADERS)
    result = []
    for row in rows:
        username = str(row.get("username", "")).strip()
        if not username:
            continue
        result.append(
            {
                "username": username,
                "display_name": str(row.get("display_name", "")).strip(),
                "pais": str(row.get("pais", "")).strip(),
                "role": str(row.get("role", "user")).strip().lower() or "user",
                "enabled": _normalize_bool(row.get("enabled"), True),
                "must_change_password": _normalize_bool(row.get("must_change_password"), False),
                "created_at": str(row.get("created_at", "")).strip(),
                "created_by": str(row.get("created_by", "")).strip(),
                "updated_at": str(row.get("updated_at", "")).strip(),
                "last_login": str(row.get("last_login", "")).strip(),
                "source": "managed",
            }
        )
    return sorted(result, key=lambda r: _normalize_username(r["username"]))


def list_secret_users() -> list[dict]:
    result = []
    for key, raw in _users_section().items():
        data = dict(raw)
        result.append(
            {
                "username": str(key),
                "display_name": str(data.get("display_name", key)),
                "pais": str(data.get("pais", "")),
                "role": str(data.get("role", "user")),
                "enabled": _normalize_bool(data.get("enabled", True), True),
                "source": "secrets",
            }
        )
    return sorted(result, key=lambda r: _normalize_username(r["username"]))


def _write_managed_row(row_index: int, record: dict) -> None:
    ws = _worksheet(MANAGED_USERS_SHEET, create=True, headers=MANAGED_USER_HEADERS)
    values = [[str(record.get(h, "")) for h in MANAGED_USER_HEADERS]]
    end_col = gspread.utils.rowcol_to_a1(1, len(MANAGED_USER_HEADERS)).rstrip("1")
    ws.update(values=values, range_name=f"A{row_index}:{end_col}{row_index}")


def audit_event(username: str, action: str, module: str, detail: str = "", pais: str = "") -> None:
    try:
        ws = _worksheet(AUDIT_SHEET, create=True, headers=AUDIT_HEADERS)
        ws.append_row(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                str(username)[:80],
                str(pais)[:80],
                str(action)[:80],
                str(module)[:80],
                str(detail)[:300],
            ],
            value_input_option="RAW",
        )
    except Exception:
        logger.exception("No fue posible registrar auditoría para accion=%s", action)


def list_audit_events(limit: int = 200) -> list[dict]:
    ws = _worksheet(AUDIT_SHEET, create=False, headers=AUDIT_HEADERS)
    if ws is None:
        return []
    rows = _rows_as_dicts(ws, AUDIT_HEADERS)
    clean = [{k: r.get(k, "") for k in AUDIT_HEADERS} for r in rows]
    return list(reversed(clean[-max(1, min(limit, 1000)) :]))


def create_managed_user(
    *,
    username: str,
    display_name: str,
    password: str,
    pais: str,
    role: str,
    enabled: bool,
    created_by: str,
    must_change_password: bool = True,
) -> tuple[bool, str]:
    normalized = suggest_username(username)
    if not re.fullmatch(r"[a-z0-9._-]{3,40}", normalized):
        return False, "No fue posible construir un usuario válido. Use al menos 3 caracteres entre letras, números, punto, guion o guion bajo."
    if _managed_user(normalized) or _secret_user(normalized):
        return False, "Ya existe un usuario con ese nombre."
    ok, message = validate_password_strength(password)
    if not ok:
        return False, message
    if role not in {"admin", "coordinator", "user"}:
        return False, "Rol no válido."

    ensure_management_store()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "username": normalized,
        "display_name": " ".join(str(display_name).split()) or normalized,
        "password_hash": hash_password(password),
        "pais": str(pais).strip(),
        "role": role,
        "enabled": str(bool(enabled)).lower(),
        "must_change_password": str(bool(must_change_password)).lower(),
        "created_at": now,
        "created_by": str(created_by),
        "updated_at": now,
        "last_login": "",
    }
    try:
        ws = _worksheet(MANAGED_USERS_SHEET, create=True, headers=MANAGED_USER_HEADERS)
        ws.append_row([record[h] for h in MANAGED_USER_HEADERS], value_input_option="RAW")
        audit_event(created_by, "CREAR_USUARIO", "Administración", f"Usuario {normalized} creado", pais)
        return True, "Usuario creado correctamente."
    except Exception:
        logger.exception("No fue posible crear usuario %s", normalized)
        return False, "No fue posible crear el usuario en el registro central."


def update_managed_user(
    username: str,
    *,
    display_name: str,
    pais: str,
    role: str,
    enabled: bool,
    updated_by: str,
) -> tuple[bool, str]:
    user = _managed_user(username)
    if not user:
        return False, "El usuario administrado no existe."
    if role not in {"admin", "coordinator", "user"}:
        return False, "Rol no válido."
    user.update(
        {
            "display_name": " ".join(str(display_name).split()) or user["username"],
            "pais": str(pais).strip(),
            "role": role,
            "enabled": str(bool(enabled)).lower(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    try:
        _write_managed_row(int(user["_row_index"]), user)
        audit_event(updated_by, "EDITAR_USUARIO", "Administración", f"Usuario {user['username']} actualizado", pais)
        return True, "Cambios guardados."
    except Exception:
        logger.exception("No fue posible actualizar usuario %s", username)
        return False, "No fue posible guardar los cambios."


def set_managed_user_password(
    username: str,
    new_password: str,
    *,
    updated_by: str,
    force_change: bool = True,
) -> tuple[bool, str]:
    user = _managed_user(username)
    if not user:
        return False, "El usuario administrado no existe."
    ok, message = validate_password_strength(new_password)
    if not ok:
        return False, message
    user["password_hash"] = hash_password(new_password)
    user["must_change_password"] = str(bool(force_change)).lower()
    user["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        _write_managed_row(int(user["_row_index"]), user)
        audit_event(updated_by, "RESTABLECER_PASSWORD", "Administración", f"Contraseña de {user['username']} actualizada", user.get("pais", ""))
        return True, "Contraseña actualizada correctamente."
    except Exception:
        logger.exception("No fue posible cambiar contraseña de %s", username)
        return False, "No fue posible actualizar la contraseña."


def change_own_password(username: str, new_password: str) -> tuple[bool, str]:
    user = _managed_user(username)
    if not user:
        return False, "No fue posible localizar su cuenta administrada."
    if verify_password(new_password, str(user.get("password_hash", ""))):
        return False, "La nueva contraseña debe ser diferente de la contraseña temporal utilizada para ingresar."

    ok, message = set_managed_user_password(
        username,
        new_password,
        updated_by=username,
        force_change=False,
    )
    if ok:
        if isinstance(st.session_state.get("auth_user"), dict):
            st.session_state.auth_user["must_change_password"] = False
        audit_event(
            username,
            "CAMBIAR_PASSWORD_PROPIO",
            "Autenticación",
            "Contraseña personal establecida correctamente",
            user.get("pais", ""),
        )
    return ok, message


def import_secret_users_to_managed(imported_by: str) -> tuple[int, int, str]:
    ok, message = ensure_management_store()
    if not ok:
        return 0, 0, message

    existing = {_normalize_username(u["username"]) for u in list_managed_users()}
    imported = 0
    skipped = 0
    ws = _worksheet(MANAGED_USERS_SHEET, create=True, headers=MANAGED_USER_HEADERS)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for username, raw in _users_section().items():
        normalized = _normalize_username(str(username))
        if normalized in existing:
            skipped += 1
            continue
        data = dict(raw)
        record = {
            "username": normalized,
            "display_name": str(data.get("display_name", username)),
            "password_hash": str(data.get("password_hash", "")),
            "pais": str(data.get("pais", "")),
            "role": str(data.get("role", "user")).strip().lower() or "user",
            "enabled": str(_normalize_bool(data.get("enabled", True), True)).lower(),
            # Los usuarios heredados conservan la contraseña temporal segura ya
            # configurada, pero deben crear una contraseña personal al primer acceso.
            "must_change_password": "true",
            "created_at": now,
            "created_by": f"import:{imported_by}",
            "updated_at": now,
            "last_login": "",
        }
        if not record["password_hash"]:
            skipped += 1
            continue
        ws.append_row([record[h] for h in MANAGED_USER_HEADERS], value_input_option="RAW")
        imported += 1
        existing.add(normalized)

    audit_event(imported_by, "IMPORTAR_USUARIOS", "Administración", f"Importados={imported}; omitidos={skipped}")
    return imported, skipped, "Migración finalizada."


def local_auth_is_configured() -> bool:
    if bool(_users_section()):
        return True
    try:
        return bool(list_managed_users())
    except Exception:
        return False


def oidc_auth_is_configured() -> bool:
    return bool(_secret_section("auth")) and bool(_secret_section("oidc_users"))


def auth_is_configured() -> bool:
    settings = get_security_settings()
    if settings.auth_mode == "oidc":
        return oidc_auth_is_configured()
    if settings.auth_mode == "both":
        return local_auth_is_configured() or oidc_auth_is_configured()
    return local_auth_is_configured()


def _clean_attempts(username: str, now: float, settings: SecuritySettings) -> None:
    store = _attempt_store()
    cutoff = now - settings.window_minutes * 60
    attempts = store["attempts"][username]
    while attempts and attempts[0] < cutoff:
        attempts.popleft()


def remaining_lockout_seconds(username: str) -> int:
    username = _normalize_username(username)
    now = time.time()
    store = _attempt_store()
    with store["lock"]:
        until = float(store["locked_until"].get(username, 0))
        if until <= now:
            store["locked_until"].pop(username, None)
            return 0
        return max(1, int(until - now))


def _record_failed_attempt(username: str, settings: SecuritySettings) -> int:
    username = _normalize_username(username)
    now = time.time()
    store = _attempt_store()
    with store["lock"]:
        _clean_attempts(username, now, settings)
        attempts = store["attempts"][username]
        attempts.append(now)
        if len(attempts) >= settings.max_attempts:
            store["locked_until"][username] = now + settings.lockout_minutes * 60
            attempts.clear()
            return settings.lockout_minutes * 60
    return 0


def _clear_attempts(username: str) -> None:
    username = _normalize_username(username)
    store = _attempt_store()
    with store["lock"]:
        store["attempts"].pop(username, None)
        store["locked_until"].pop(username, None)


def _sync_legacy_session(user: dict) -> None:
    """Compatibilidad con páginas v1 durante la transición."""
    st.session_state.logueado = True
    st.session_state.verificado = True
    st.session_state.usuario = str(user.get("username", ""))
    st.session_state.pais_usuario = str(user.get("pais", ""))


def _update_last_login(user: dict) -> None:
    if user.get("source") != "managed" or not user.get("_row_index"):
        return
    try:
        user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_managed_row(int(user["_row_index"]), user)
    except Exception:
        logger.exception("No fue posible actualizar last_login de %s", user.get("username"))


def _upgrade_legacy_imported_user_for_first_login(user: dict) -> dict:
    """Activa una sola vez el cambio obligatorio para usuarios migrados con v2.2.x.

    Las versiones anteriores importaban desde Secrets con ``must_change_password=false``.
    Esos registros nacían con ``created_at == updated_at``. Al primer acceso después de
    esta actualización, se marca el cambio obligatorio y se actualiza ``updated_at``.
    Después de que el usuario crea su contraseña personal, el registro vuelve a false
    y no se vuelve a activar automáticamente.
    """
    if not user or user.get("source") != "managed":
        return user
    if bool(user.get("must_change_password", False)):
        return user
    created_by = str(user.get("created_by", "")).strip().lower()
    if not created_by.startswith("import:"):
        return user

    created_at = str(user.get("created_at", "")).strip()
    updated_at = str(user.get("updated_at", "")).strip()
    # Registros importados por la versión anterior no habían sido modificados después
    # de su migración. Este control evita volver a forzar a quien ya actualizó su clave.
    if created_at and updated_at and created_at != updated_at:
        return user

    try:
        user["must_change_password"] = "true"
        user["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_managed_row(int(user["_row_index"]), user)
        audit_event(
            user.get("username", ""),
            "ACTIVAR_CAMBIO_INICIAL_PASSWORD",
            "Autenticación",
            "Usuario migrado: cambio de contraseña requerido en el primer acceso",
            user.get("pais", ""),
        )
        user["must_change_password"] = True
    except Exception:
        # No se bloquea el acceso por una migración de metadatos; queda registro en logs
        # y el administrador puede forzar el cambio desde el panel.
        logger.exception("No fue posible activar cambio inicial para %s", user.get("username"))
    return user


def force_first_login_password_change_for_imported_users(updated_by: str) -> tuple[int, int, str]:
    """Activa una sola vez el cambio obligatorio para cuentas heredadas ya migradas.

    La acción queda registrada en la bitácora. Así, aunque luego cada usuario cambie su
    contraseña y su bandera vuelva a ``false``, pulsar nuevamente el botón no los fuerza
    otra vez. Los usuarios que se importen después ya nacen con el cambio obligatorio.
    """
    ws = _worksheet(MANAGED_USERS_SHEET, create=False, headers=MANAGED_USER_HEADERS)
    if ws is None:
        return 0, 0, "No se encontró la hoja de usuarios administrados."

    marker_action = "ROTACION_INICIAL_MIGRADOS_V224"
    try:
        audit_ws = _worksheet(AUDIT_SHEET, create=True, headers=AUDIT_HEADERS)
        audit_rows = _rows_as_dicts(audit_ws, AUDIT_HEADERS)
        if any(str(r.get("accion", "")).strip() == marker_action for r in audit_rows):
            return 0, 0, "Esta actualización de seguridad ya fue aplicada anteriormente."
    except Exception:
        logger.exception("No fue posible comprobar el marcador de rotación inicial")
        return 0, 0, "No fue posible verificar el estado de la actualización de seguridad."

    changed = 0
    skipped = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        rows = _rows_as_dicts(ws, MANAGED_USER_HEADERS)
        for row in rows:
            created_by = str(row.get("created_by", "")).strip().lower()
            already_pending = _normalize_bool(row.get("must_change_password"), False)
            if not created_by.startswith("import:") or already_pending:
                skipped += 1
                continue
            row["must_change_password"] = "true"
            row["updated_at"] = now
            _write_managed_row(int(row["_row_index"]), row)
            changed += 1

        audit_event(
            updated_by,
            marker_action,
            "Administración",
            f"Marcados={changed}; omitidos={skipped}",
        )
        if changed:
            return changed, skipped, "Cambio obligatorio activado para los usuarios migrados pendientes."
        return changed, skipped, "No se encontraron usuarios migrados pendientes de esta actualización."
    except Exception:
        logger.exception("No fue posible marcar usuarios migrados para cambio de contraseña")
        return changed, skipped, "No fue posible actualizar el estado de los usuarios migrados."


def authenticate(username: str, password: str) -> tuple[bool, str]:
    settings = get_security_settings()
    normalized = _normalize_username(username)
    if not normalized or not password:
        return False, "Ingrese usuario y contraseña."

    remaining = remaining_lockout_seconds(normalized)
    if remaining:
        minutes = max(1, (remaining + 59) // 60)
        return False, f"Acceso temporalmente bloqueado. Intente nuevamente en aproximadamente {minutes} min."

    user = _managed_user(normalized)
    if user is None:
        user = _secret_user(normalized)

    valid = bool(
        user
        and user.get("enabled", True)
        and verify_password(password, str(user.get("password_hash", "")))
    )

    if not valid:
        locked_for = _record_failed_attempt(normalized, settings)
        logger.warning("Intento de acceso fallido para usuario=%s", normalized)
        if locked_for:
            return False, f"Demasiados intentos fallidos. Acceso bloqueado por {settings.lockout_minutes} minutos."
        return False, "Usuario o contraseña incorrectos."

    _clear_attempts(normalized)
    if user.get("source") == "managed":
        # Solo después de validar correctamente la contraseña se aplica la migración
        # de seguridad a cuentas heredadas de versiones anteriores.
        user = _upgrade_legacy_imported_user_for_first_login(user)

    session_user = {
        "username": user["username"],
        "display_name": str(user.get("display_name", user["username"])),
        "pais": str(user.get("pais", "")),
        "role": str(user.get("role", "user")).lower(),
        "source": str(user.get("source", "secrets")),
        "must_change_password": bool(user.get("must_change_password", False)),
    }
    st.session_state.authenticated = True
    st.session_state.auth_user = session_user
    _sync_legacy_session(session_user)
    st.session_state.last_activity = time.time()
    _update_last_login(user)
    audit_event(session_user["username"], "LOGIN_OK", "Autenticación", "Inicio de sesión correcto", session_user.get("pais", ""))
    logger.info("Inicio de sesión correcto para usuario=%s", normalized)
    return True, "Acceso autorizado."


def _oidc_user_record() -> dict | None:
    try:
        if not st.user.is_logged_in:
            return None
        email = str(getattr(st.user, "email", "") or st.user.get("email", "")).strip().lower()
    except Exception:
        return None
    if not email:
        return None

    section = _secret_section("oidc_users") or {}
    for key, raw in section.items():
        if str(key).strip().lower() != email:
            continue
        data = dict(raw)
        if not data.get("enabled", True):
            return None
        return {
            "username": email,
            "display_name": str(data.get("display_name") or getattr(st.user, "name", "") or email),
            "pais": str(data.get("pais", "")),
            "role": str(data.get("role", "user")).lower(),
            "auth_method": "oidc",
            "source": "oidc",
            "must_change_password": False,
        }
    return None


def current_user() -> dict | None:
    settings = get_security_settings()
    if settings.auth_mode in {"oidc", "both"}:
        oidc_user = _oidc_user_record()
        if oidc_user:
            st.session_state.authenticated = True
            st.session_state.auth_user = oidc_user
            _sync_legacy_session(oidc_user)
            st.session_state.setdefault("last_activity", time.time())
            return oidc_user
        if settings.auth_mode == "oidc":
            return None

    if not st.session_state.get("authenticated", False):
        return None
    user = st.session_state.get("auth_user")
    if isinstance(user, dict):
        _sync_legacy_session(user)
        return dict(user)
    return None


def logout() -> None:
    user = current_user()
    if user:
        audit_event(user.get("username", ""), "LOGOUT", "Autenticación", "Cierre de sesión", user.get("pais", ""))
    is_oidc = bool(user and user.get("auth_method") == "oidc")
    st.session_state.clear()
    if is_oidc:
        try:
            st.logout()
        except Exception:
            logger.exception("No se pudo completar st.logout()")


def require_auth(*, allow_password_change: bool = False) -> dict:
    user = current_user()
    if not user:
        st.warning("🔐 Su sesión no está autenticada. Regrese al inicio e ingrese sus credenciales.")
        if st.button("Ir al inicio", type="primary"):
            st.switch_page("Home.py")
        st.stop()

    settings = get_security_settings()
    now = time.time()
    last_activity = float(st.session_state.get("last_activity", now))
    if now - last_activity > settings.session_timeout_minutes * 60:
        st.session_state.clear()
        st.warning("La sesión expiró por inactividad. Inicie sesión nuevamente.")
        if st.button("Volver al inicio", type="primary"):
            st.switch_page("Home.py")
        st.stop()

    st.session_state.last_activity = now
    _sync_legacy_session(user)

    # No permite saltarse el cambio obligatorio entrando directamente a ERSI/QR.
    # Home pasa allow_password_change=True porque allí se muestra el formulario seguro.
    if (
        user.get("source") == "managed"
        and user.get("must_change_password")
        and not allow_password_change
    ):
        st.info("Por seguridad, primero debe crear su contraseña personal.")
        try:
            st.switch_page("Home.py")
        except Exception:
            st.warning("Regrese al inicio para completar el cambio de contraseña.")
        st.stop()

    return user


def require_role(*roles: str) -> dict:
    user = require_auth()
    allowed = {str(r).strip().lower() for r in roles}
    if str(user.get("role", "user")).lower() not in allowed:
        st.error("No tiene permisos para acceder a este módulo.")
        if st.button("Volver al inicio", type="primary"):
            st.switch_page("Home.py")
        st.stop()
    return user
