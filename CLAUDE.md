# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Flask app (port 5003) for institutional audit normative analysis — OFS Tlaxcala. Users query an audit knowledge base; the app returns relevant irregularity types, required documentation, and applicable legal norms.

**Key layers:**
- `app.py` — Flask app, `Config` class, `SistemaCache` (LRU, MD5-keyed), `MonitorRendimiento`, `MotorBusquedaNormativasMejorado` (TF-IDF/sklearn), and all routes
- `scripts/auth.py` — session-based auth; reads users from `shared_user_catalog` (portfolio-wide catalog at `/home/gabo/portfolio/projects/catalogos/catalogo_usuarios.json`); do not duplicate auth logic in `app.py`
- `scripts/utils.py` — `AUDITORIA_DATA` dict: JSON audit databases embedded as raw strings (avoids file I/O at runtime)
- `config.py` — only exports `PORT = 5003`
- `templates/` — `login.html` and `index.html` (institutional OFS design)

**Data flow:** On startup, `cargar_bases_datos()` pulls JSON from `AUDITORIA_DATA`, builds a unified TF-IDF corpus across all audit types ("Obra Pública", "Financiera"). Queries hit `SistemaCache` first, then `MotorBusquedaNormativasMejorado.buscar_semanticamente()`, which filters by audit type and returns top-N results by cosine similarity.

**Auth:** `login_required` decorator redirects unauthenticated requests to `/login`. `SECRET_KEY` must come from `.env` or `/etc/default/portfolio-auditel` — no hardcoded default.

## Development Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set SECRET_KEY

# Run
python3 app.py         # http://127.0.0.1:5003

# Tests
venv/bin/pytest tests/ -v
venv/bin/pytest tests/test_app.py::test_health_standard_route -v  # single test
```

## Constraints

- Do not edit `static/css/style.css` without explicit instruction — it's the institutional OFS design.
- Auth logic lives in `scripts/auth.py` only — do not add auth checks or credential handling in `app.py`.
- Logs go in `logs/` (not `log/`). The directory is created automatically on startup.
- `SECRET_KEY` has no hardcoded fallback by design.

## Deploy

```bash
sudo systemctl restart portfolio-auditel
curl http://localhost:5003/api/health
```

Systemd unit, NGINX config, and env file templates are in `deploy/`.
