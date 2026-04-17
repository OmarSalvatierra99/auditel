# Auditel Institucional

Herramienta de análisis normativo inteligente para el Órgano de Fiscalización Superior del Estado de Tlaxcala. Motor de búsqueda TF-IDF sobre bases de datos de normatividad de Obra Pública y Financiera.

**Stack:** Flask 3 + scikit-learn + SQLite  
**Puerto:** 5003  
**Servicio:** `portfolio-auditel`

---

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución local

```bash
cp .env.example .env
# Editar .env con SECRET_KEY
python app.py
```

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `SECRET_KEY` | Sí | Clave secreta Flask (mín. 32 chars) |
| `catalogos/catalogo_usuarios.json` | Sí | Catálogo compartido de usuarios del workspace |
| `PORT` | Sí | Puerto del servidor (5003) |

## Healthcheck

```
GET /api/health  →  JSON con estado de bases de datos y motor de búsqueda
```

## Tests

```bash
venv/bin/pytest tests/ -v
```

---

© 2026 Omar Gabriel Salvatierra Garcia
