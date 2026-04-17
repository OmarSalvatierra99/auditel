# CLAUDE.md — Auditel

## Contexto de trabajo
Proyecto Flask institucional (OFS Tlaxcala). Análisis normativo con TF-IDF/sklearn.

## Reglas
- No tocar `static/css/style.css` sin instrucción explícita (diseño institucional OFS)
- `SECRET_KEY` sin default hardcodeado — va en `/etc/default/portfolio-auditel`
- Auth: `scripts/auth.py` — no duplicar lógica de autenticación en `app.py`
- Logs en `logs/` — no `log/`

## Testing
```bash
venv/bin/pytest tests/ -v
```

## Deploy
```bash
sudo systemctl restart portfolio-auditel
curl http://localhost:5003/api/health
```
