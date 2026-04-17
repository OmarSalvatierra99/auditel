"""
Auditel — Autenticación
========================
Autenticación por sesión basada en USER_CREDENTIALS env var.
Formato: "usuario1:clave1,usuario2:clave2"
"""

import os
import sys
from functools import wraps
from pathlib import Path

from flask import redirect, request, session, url_for

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from werkzeug.security import check_password_hash, generate_password_hash

from shared_user_catalog import list_users

PROJECT_KEY = "03-auditel"

USER_PRIORITY = {
    "luis": 0,
    "gabo": 1,
}


def _normalize(value: str) -> str:
    return str(value or "").strip().casefold()


def _load_env_users() -> dict[str, dict[str, str]]:
    users: dict[str, dict[str, str]] = {}
    for user in list_users(project_key=PROJECT_KEY):
        username = str(user.get("usuario") or "").strip()
        password = str(user.get("clave") or "").strip()
        display_name = str(user.get("nombre_completo") or username).strip()
        normalized_username = _normalize(username)
        if not normalized_username:
            continue

        users[normalized_username] = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "display_name": display_name or username,
        }

    return users


def _build_user_map() -> dict[str, dict[str, str]]:
    return _load_env_users()


def get_users() -> dict[str, str]:
    """Retorna dict {username: password} con usuarios disponibles para login."""
    return {
        payload["username"]: payload["password"]
        for payload in _build_user_map().values()
    }


def get_authorized_users() -> list[dict[str, str]]:
    """Retorna usuarios visibles en la pantalla de acceso institucional."""
    authorized_users = list(_build_user_map().values())
    authorized_users.sort(
        key=lambda user: (
            USER_PRIORITY.get(_normalize(user["username"]), 99),
            _normalize(user["display_name"]),
        )
    )
    return authorized_users


def get_user_display_name(username: str, fallback: str = "") -> str:
    """Retorna el nombre de despliegue institucional del usuario."""
    normalized_username = _normalize(username)
    user = _build_user_map().get(normalized_username)
    if user:
        return user["display_name"]
    return fallback or str(username or "").strip()


def authenticate(username: str, password: str) -> bool:
    """Verifica credenciales. Retorna True si son válidas."""
    user = _build_user_map().get(_normalize(username))
    if not user:
        return False
    return check_password_hash(user["password_hash"], password.strip())


def get_canonical_username(username: str) -> str | None:
    """Retorna el nombre de usuario canónico, o None si no existe."""
    user = _build_user_map().get(_normalize(username))
    if not user:
        return None
    return user["username"]


def is_authenticated() -> bool:
    """Verifica que la sesión activa corresponda a un usuario válido."""
    current_username = session.get("auth_user") or session.get("usuario")
    return get_canonical_username(current_username or "") is not None


def login_required(f):
    """Decorador que redirige al login si no hay sesión activa."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.method == "GET":
                next_url = request.full_path if request.query_string else request.path
            else:
                next_url = request.referrer or url_for("index")
            return redirect(url_for("login", next=next_url))
        return f(*args, **kwargs)

    return decorated
