from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

import streamlit as st

logger = logging.getLogger(__name__)

DEFAULT_ITERATIONS = 600_000
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_WINDOW_MINUTES = 15
DEFAULT_LOCKOUT_MINUTES = 10
DEFAULT_SESSION_TIMEOUT_MINUTES = 30


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
    import secrets

    salt = secrets.token_bytes(16)
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


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _get_user(username: str) -> dict | None:
    target = _normalize_username(username)
    for key, raw in _users_section().items():
        if _normalize_username(str(key)) != target:
            continue
        data = dict(raw)
        data["username"] = str(key)
        data.setdefault("display_name", str(key))
        data.setdefault("pais", "")
        data.setdefault("enabled", True)
        return data
    return None


def local_auth_is_configured() -> bool:
    return bool(_users_section())


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


def authenticate(username: str, password: str) -> tuple[bool, str]:
    settings = get_security_settings()
    normalized = _normalize_username(username)
    if not normalized or not password:
        return False, "Ingrese usuario y contraseña."

    remaining = remaining_lockout_seconds(normalized)
    if remaining:
        minutes = max(1, (remaining + 59) // 60)
        return False, f"Acceso temporalmente bloqueado. Intente nuevamente en aproximadamente {minutes} min."

    user = _get_user(normalized)
    # Respuesta uniforme para evitar revelar si un usuario existe.
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
    st.session_state.authenticated = True
    st.session_state.auth_user = {
        "username": user["username"],
        "display_name": str(user.get("display_name", user["username"])),
        "pais": str(user.get("pais", "")),
        "role": str(user.get("role", "user")),
    }
    st.session_state.pais_usuario = str(user.get("pais", ""))
    st.session_state.usuario = user["username"]
    st.session_state.last_activity = time.time()
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
            "role": str(data.get("role", "user")),
            "auth_method": "oidc",
        }
    return None


def current_user() -> dict | None:
    settings = get_security_settings()
    if settings.auth_mode in {"oidc", "both"}:
        oidc_user = _oidc_user_record()
        if oidc_user:
            st.session_state.authenticated = True
            st.session_state.auth_user = oidc_user
            st.session_state.pais_usuario = oidc_user.get("pais", "")
            st.session_state.usuario = oidc_user.get("username", "")
            st.session_state.setdefault("last_activity", time.time())
            return oidc_user
        if settings.auth_mode == "oidc":
            return None

    if not st.session_state.get("authenticated", False):
        return None
    user = st.session_state.get("auth_user")
    return dict(user) if isinstance(user, dict) else None


def logout() -> None:
    user = current_user()
    is_oidc = bool(user and user.get("auth_method") == "oidc")
    st.session_state.clear()
    if is_oidc:
        try:
            st.logout()
        except Exception:
            logger.exception("No se pudo completar st.logout()")


def require_auth() -> dict:
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
        logout()
        st.warning("⌛ La sesión expiró por inactividad. Inicie sesión nuevamente.")
        if st.button("Volver al inicio", type="primary"):
            st.switch_page("Home.py")
        st.stop()

    st.session_state.last_activity = now
    return user
