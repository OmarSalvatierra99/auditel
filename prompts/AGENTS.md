# AGENTS.md — Auditel

## Identidad del proyecto
**Slug:** auditel | **Puerto:** 5003 | **Stack:** Flask 3 + scikit-learn + SQLite  
**Servicio:** `portfolio-auditel` | **EnvironmentFile:** `/etc/default/portfolio-auditel`

## Descripción
Herramienta institucional de análisis normativo para auditorías (OFS Tlaxcala). Motor de búsqueda TF-IDF sobre bases de datos de normatividad de Obra Pública y Financiera.

## Auth
- `scripts/auth.py` — `USER_CREDENTIALS` env var + usuario institucional `luis` por defecto
- `is_authenticated()` busca `session["auth_user"]` o `session["usuario"]`
- `login_required` decorador con soporte `?next=` para redirigir post-login
- Login UI: `templates/login.html` — panel de usuarios activos + panel de contraseña

## Rutas protegidas
Todas requieren login excepto `/login`, `/logout`, `/api/health`, `/health`.

## Consideraciones críticas
- `SECRET_KEY` debe estar en `/etc/default/portfolio-auditel` — sin default en código
- Motor TF-IDF se inicializa al arrancar; puede tardar varios segundos
- 2 workers gunicorn (sin WebSockets)
- `logs/` (no `log/`) — ya corregido en `configurar_logging_detallado()`

## Healthcheck
`GET /api/health` — retorna JSON con estado de las bases de datos y el motor de búsqueda
