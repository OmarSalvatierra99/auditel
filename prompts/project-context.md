# Contexto del proyecto — Auditel

## Descripción
Sistema de análisis normativo inteligente para el Órgano de Fiscalización Superior del Estado de Tlaxcala. Permite a auditores buscar y analizar criterios normativos de Obra Pública y Financiera mediante búsqueda semántica TF-IDF.

## Usuarios
- **C.P. Luis Felipe Camilo Fuentes** (`luis`) — usuario institucional principal

## Datos
- `scripts/utils.py` — carga y estructura las bases de datos de normatividad (`AUDITORIA_DATA`)
- Tipos: `Obra Pública`, `Financiera`
- Motor TF-IDF con caché de búsquedas (`cache_busqueda`)

## Estado de migración
- Migrado en wave 2 (2026-04-13)
- Login añadido: `templates/login.html` + `scripts/auth.py`
- `log/` renombrado a `logs/`
