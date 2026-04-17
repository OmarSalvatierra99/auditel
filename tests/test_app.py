"""Tests para Auditel (03-auditel)."""
import os
import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("FLASK_ENV", "testing")


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_standard_route(client):
    """GET /api/health debe retornar 200."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] in ("healthy", "degraded")


def test_health_compat_route(client):
    """GET /health también debe retornar 200."""
    r = client.get("/health")
    assert r.status_code == 200


def test_index_redirects_when_not_logged_in(client):
    """GET / sin sesión debe redirigir al login."""
    r = client.get("/")
    assert r.status_code == 302
    assert "login" in r.headers["Location"]


def test_login_page_loads(client):
    """GET /login debe cargar el formulario de acceso."""
    r = client.get("/login")
    assert r.status_code == 200


def test_login_with_default_institutional_user(client):
    """POST /login con usuario institucional 'luis' y clave por defecto debe redirigir."""
    r = client.post("/login", data={"username": "luis", "password": "luis2025"})
    assert r.status_code == 302


def test_login_with_invalid_credentials(client):
    """POST /login con credenciales incorrectas debe volver al login."""
    r = client.post("/login", data={"username": "luis", "password": "wrongpass"})
    assert r.status_code == 200


def test_auth_functions():
    """Verifica que authenticate y get_canonical_username funcionen correctamente."""
    from scripts.auth import authenticate, get_canonical_username, get_authorized_users

    assert authenticate("luis", "luis2025") is True
    assert authenticate("luis", "wrong") is False
    assert get_canonical_username("LUIS") == "luis"
    assert get_canonical_username("noexiste") is None

    users = get_authorized_users()
    assert any(u["username"] == "luis" for u in users)


def test_logout_clears_session(client):
    """POST /logout debe limpiar la sesión y redirigir al login."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"
    r = client.post("/logout")
    assert r.status_code == 302
    assert "login" in r.headers["Location"]
