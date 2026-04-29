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


def test_index_logged_in_shows_clear_chat_button(client):
    """La pantalla principal debe incluir el botón para limpiar el chat."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"

    r = client.get("/")
    assert r.status_code == 200
    assert b"Limpiar chat" in r.data


def test_index_logged_in_hides_internal_setup_copy(client):
    """La interfaz pública no debe mostrar texto técnico de preparación interna."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"

    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Chatbot Normativo" in html
    assert 'value="auto"' in html
    assert "Qwen Chat" not in html
    assert "Proveedor previsto" not in html
    assert "Estado Qwen" not in html
    assert "La interfaz ya quedó preparada para Qwen" not in html
    assert "Escribe <strong>/</strong> para elegir contexto" in html
    assert '"label": "Obra P\\u00fablica"' in html
    assert '"label": "Financiero"' in html


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


def test_external_excel_sources_are_loaded():
    """Las carpetas nuevas deben incorporarse como fuente adicional de datos."""
    from scripts.utils import AUDITORIA_DATA

    financieros_excel = [
        item for item in AUDITORIA_DATA["Financiera"]
        if item.get("origen_fuente") == "excel_financiero_conceptos"
    ]
    obra_excel = [
        item for item in AUDITORIA_DATA["Obra Pública"]
        if item.get("origen_fuente") == "excel_obra_publica_conceptos"
    ]

    assert financieros_excel
    assert obra_excel
    assert any(item.get("concepto") for item in financieros_excel)
    assert any(item.get("concepto") for item in obra_excel)


def test_generar_analisis_por_concepto_activa_modo_solo_normativa():
    """Una consulta por concepto debe responder sólo con normativas."""
    from app import generar_analisis_normativo

    analisis = generar_analisis_normativo(
        "¿Cuál es la normativa para No presentan pólizas?",
        "Financiera",
    )

    assert analisis["encontrado"] is True
    assert analisis["solo_normativa"] is True
    assert analisis["normativas"]


def test_formatear_respuesta_por_concepto_omite_descripcion_y_tipo():
    """El formateo por concepto no debe exponer tipo ni descripción."""
    from app import formatear_respuesta_normativa

    respuesta = formatear_respuesta_normativa({
        "encontrado": True,
        "solo_normativa": True,
        "normativas": [
            {
                "tipo_irregularidad": "No presentan pólizas",
                "concepto": "No presentan pólizas",
                "descripcion": "Texto que no debe mostrarse",
                "normativas": {
                    "Normatividad Local": "Artículo 15 de prueba"
                },
                "puntaje_similitud": 0.95,
                "categoria": "General",
                "subcategoria": "",
            }
        ],
    })

    assert "Artículo 15 de prueba" in respuesta
    assert "Texto que no debe mostrarse" not in respuesta
    assert "No presentan pólizas" not in respuesta
    assert "Descripción" not in respuesta


def test_generar_analisis_descarta_consulta_generica_de_licitacion_en_obra_publica():
    """No debe inventar coincidencias para consultas generales sin respaldo real."""
    from app import generar_analisis_normativo

    analisis = generar_analisis_normativo(
        "licitacion obra publica",
        "Obra Pública",
        "No aplica",
    )

    assert analisis["encontrado"] is False
    assert "licitación" in analisis["mensaje"].lower() or "contratación" in analisis["mensaje"].lower()


def test_generar_analisis_deduplica_resultado_repetido_en_obra_publica():
    """No debe devolver dos veces la misma irregularidad desde fuentes distintas."""
    from app import generar_analisis_normativo

    analisis = generar_analisis_normativo(
        "conceptos pagados no ejecutados",
        "Obra Pública",
        "No aplica",
    )

    tipos = [item["tipo_irregularidad"] for item in analisis["normativas"]]
    assert tipos.count("Conceptos de obra pagados no ejecutados") == 1


def test_ask_devuelve_respuesta_compacta_sin_enlaces_externos(client):
    """La respuesta principal no debe incluir ruido visual ni enlaces automáticos."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"

    r = client.post("/ask", data={
        "question": "conceptos pagados no ejecutados",
        "auditoria": "Obra Pública",
        "ente": "No aplica",
    })

    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert "Fuentes oficiales" not in data["answer"]
    assert "Patrones detectados" not in data["answer"]
    assert "Estadísticas del análisis" not in data["answer"]
    assert "analysis-response" in data["answer"]


def test_ask_admite_modo_unificado_auto(client):
    """El chat debe poder consultar la base unificada sin selector visible."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"

    r = client.post("/ask", data={
        "question": "conceptos pagados no ejecutados",
        "auditoria": "auto",
        "ente": "No aplica",
    })

    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["auditoria_label"] == "Base unificada"
    assert "Obra Pública" in data["auditorias_consultadas"]


def test_logout_clears_session(client):
    """POST /logout debe limpiar la sesión y redirigir al login."""
    with client.session_transaction() as sess:
        sess["auth_user"] = "luis"
        sess["usuario"] = "luis"
    r = client.post("/logout")
    assert r.status_code == 302
    assert "login" in r.headers["Location"]
