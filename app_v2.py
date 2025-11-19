"""
Auditel v3.0 - Sistema Inteligente de Análisis Normativo con Web Scraping
Aplicación refactorizada con arquitectura modular y web scraping funcional
"""
import os
import json
import re
import logging
import time
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash

# Importaciones de módulos propios
from config.settings import Config, AuditoriaConfig
from scrapers.scraper_manager import get_scraper_manager
from utils.cache_manager import CacheManager
from utils.text_processor import TextProcessor
from models.normativa import Normativa

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

def configurar_logging():
    """Configura logging mejorado"""
    os.makedirs(Config.LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s | [%(filename)s:%(lineno)d]'
    )

    # Handler para archivo
    file_handler = RotatingFileHandler(
        os.path.join(Config.LOG_DIR, 'auditel.log'),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Handler consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configurar logger principal
    logger = logging.getLogger('auditel')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Reducir ruido de librerías externas
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return logger

logger = configurar_logging()

# =============================================================================
# INICIALIZACIÓN DE FLASK
# =============================================================================

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# =============================================================================
# INICIALIZACIÓN DE COMPONENTES GLOBALES
# =============================================================================

# Gestor de caché
cache_manager = CacheManager(cache_dir=Config.CACHE_DIR, expiration_hours=24)

# Gestor de scrapers
scraper_manager = get_scraper_manager(cache_manager=cache_manager)

# Procesador de texto
text_processor = TextProcessor()

# Base de datos local (JSON)
DB_AUDITORIA = {}
ESTADISTICAS_DB = {}

# Motor de búsqueda local
class MotorBusquedaLocal:
    """Motor de búsqueda para datos locales (JSON)"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=['el', 'la', 'de', 'en', 'y', 'o', 'un', 'una', 'es', 'son'],
            min_df=1,
            max_df=0.9,
            max_features=Config.TFIDF_MAX_FEATURES
        )
        self.matriz_tfidf = None
        self.metadatos = []
        self._inicializado = False

    def preparar_datos(self, datos_auditoria):
        """Prepara datos locales para búsqueda"""
        documentos = []
        self.metadatos = []

        for auditoria, items in datos_auditoria.items():
            for item in items:
                texto = self._crear_documento(item)
                documentos.append(texto)
                self.metadatos.append({
                    'auditoria': auditoria,
                    'item': item
                })

        if documentos:
            try:
                self.matriz_tfidf = self.vectorizer.fit_transform(documentos)
                self._inicializado = True
                logger.info(f"Motor local preparado: {len(documentos)} documentos")
            except Exception as e:
                logger.error(f"Error preparando motor local: {e}")
                self._inicializado = False

    def _crear_documento(self, item):
        """Crea documento de texto para búsqueda"""
        campos = [
            item.get('tipo', ''),
            item.get('descripcion_irregularidad', ''),
            item.get('categoria', ''),
            item.get('subcategoria', '')
        ]

        for key, val in item.items():
            if 'normatividad' in key.lower() and val:
                campos.append(str(val))

        return ' '.join(filter(None, campos))

    def buscar(self, consulta, auditoria_tipo, top_n=6):
        """Busca en datos locales"""
        if not self._inicializado:
            return []

        try:
            consulta_tfidf = self.vectorizer.transform([consulta])
            similitudes = cosine_similarity(consulta_tfidf, self.matriz_tfidf).flatten()

            resultados = []
            for idx, similitud in enumerate(similitudes):
                meta = self.metadatos[idx]
                if similitud > Config.SIMILARITY_THRESHOLD and meta['auditoria'] == auditoria_tipo:
                    resultados.append({
                        'item': meta['item'],
                        'similitud': float(similitud),
                        'indice': idx
                    })

            resultados.sort(key=lambda x: x['similitud'], reverse=True)
            return resultados[:top_n]

        except Exception as e:
            logger.error(f"Error en búsqueda local: {e}")
            return []

motor_busqueda_local = MotorBusquedaLocal()

# =============================================================================
# CARGA DE DATOS LOCALES
# =============================================================================

def cargar_bases_datos():
    """Carga bases de datos JSON locales"""
    if not os.path.exists(Config.DATA_DIR):
        logger.error(f"Directorio {Config.DATA_DIR} no encontrado")
        return {}, {}

    bases = {}
    stats = {}

    for nombre, config in AuditoriaConfig.TIPOS.items():
        file_path = os.path.join(Config.DATA_DIR, config["archivo"])
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)

                    if isinstance(datos, list):
                        bases[nombre] = datos
                        stats[nombre] = {
                            'registros': len(datos),
                            'descripcion': config['descripcion']
                        }
                        logger.info(f"✅ {nombre}: {len(datos)} registros")
            except Exception as e:
                logger.error(f"Error cargando {file_path}: {e}")

    return bases, stats

DB_AUDITORIA, ESTADISTICAS_DB = cargar_bases_datos()
motor_busqueda_local.preparar_datos(DB_AUDITORIA)

# =============================================================================
# SISTEMA DE BÚSQUEDA HÍBRIDO (LOCAL + WEB SCRAPING)
# =============================================================================

def buscar_hibrido(query, auditoria_tipo, usar_web_scraping=True):
    """
    Búsqueda híbrida que combina datos locales con web scraping

    Args:
        query: Consulta de búsqueda
        auditoria_tipo: Tipo de auditoría
        usar_web_scraping: Si activar web scraping

    Returns:
        Dict con resultados locales y web
    """
    resultados = {
        'locales': [],
        'web': [],
        'total': 0,
        'fuentes_web': [],
        'tiempo_web': 0
    }

    # 1. Buscar en datos locales
    logger.info(f"Buscando localmente: {query}")
    resultados_locales = motor_busqueda_local.buscar(query, auditoria_tipo, top_n=6)
    resultados['locales'] = resultados_locales
    logger.info(f"Resultados locales: {len(resultados_locales)}")

    # 2. Buscar en web si está habilitado
    if usar_web_scraping:
        try:
            logger.info(f"Iniciando web scraping: {query}")
            inicio_web = time.time()

            # Buscar en todas las fuentes
            resultado_web = scraper_manager.buscar_en_todos(
                query=query,
                max_resultados_por_fuente=3,
                usar_cache=True
            )

            resultados['web'] = [n.to_dict() for n in resultado_web.normativas]
            resultados['fuentes_web'] = resultado_web.fuentes_consultadas
            resultados['tiempo_web'] = time.time() - inicio_web

            logger.info(
                f"Web scraping completado: {len(resultado_web.normativas)} "
                f"resultados en {resultados['tiempo_web']:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error en web scraping: {e}", exc_info=True)

    resultados['total'] = len(resultados['locales']) + len(resultados['web'])
    return resultados

# =============================================================================
# GENERACIÓN DE RESPUESTAS MEJORADAS
# =============================================================================

def generar_respuesta_completa(query, auditoria_tipo, ente_tipo, resultados_hibridos):
    """Genera respuesta combinando resultados locales y web"""

    respuesta = f"""
## 🔍 Análisis Normativo Completo

**📊 Tipo de Auditoría:** {auditoria_tipo}
**📋 Tipo de Ente:** {ente_tipo or "No especificado"}
**🔎 Consulta:** {query}

---

"""

    # Resultados locales
    if resultados_hibridos['locales']:
        respuesta += f"""
### 📁 Resultados de Base de Datos Local ({len(resultados_hibridos['locales'])} encontrados)

"""
        for i, resultado in enumerate(resultados_hibridos['locales'][:4], 1):
            item = resultado['item']
            similitud = resultado['similitud']

            relevancia = "🟢 Alta" if similitud > 0.5 else "🟡 Media" if similitud > 0.2 else "🔴 Baja"

            respuesta += f"""
#### {i}. {item.get('tipo', 'Sin tipo')} {relevancia}

**📝 Descripción:** {item.get('descripcion_irregularidad', 'No disponible')}

**⚖️ Normativas aplicables:**
"""
            # Agregar normativas específicas según tipo de auditoría
            config = AuditoriaConfig.TIPOS.get(auditoria_tipo, {})
            for campo in config.get('campos_normativas', []):
                if item.get(campo):
                    nombre_campo = campo.replace('_', ' ').title()
                    respuesta += f"- **{nombre_campo}:** {item[campo]}\n"

            respuesta += "\n---\n"

    # Resultados web
    if resultados_hibridos['web']:
        respuesta += f"""
### 🌐 Resultados de Web Scraping ({len(resultados_hibridos['web'])} encontrados)

**Fuentes consultadas:** {', '.join(resultados_hibridos['fuentes_web'])}
**Tiempo de búsqueda:** {resultados_hibridos['tiempo_web']:.2f}s

"""
        for i, norm_dict in enumerate(resultados_hibridos['web'][:4], 1):
            respuesta += f"""
#### {i}. {norm_dict.get('titulo', 'Sin título')}

**📰 Fuente:** {norm_dict.get('fuente', 'Desconocida')}
**📅 Fecha:** {norm_dict.get('fecha_publicacion', 'No especificada')}
**📝 Contenido:** {text_processor.resumen_texto(norm_dict.get('contenido', ''), 200)}

"""
            if norm_dict.get('url'):
                respuesta += f"**🔗 URL:** [{norm_dict['url']}]({norm_dict['url']})\n"

            if norm_dict.get('keywords'):
                keywords = ', '.join(norm_dict['keywords'][:5])
                respuesta += f"**🏷️ Keywords:** {keywords}\n"

            respuesta += "\n---\n"

    # Estadísticas finales
    respuesta += f"""
---
**📈 Estadísticas del Análisis:**
• **Total de normativas encontradas:** {resultados_hibridos['total']}
• **Resultados locales:** {len(resultados_hibridos['locales'])}
• **Resultados web:** {len(resultados_hibridos['web'])}
• **Fuentes web consultadas:** {len(resultados_hibridos.get('fuentes_web', []))}
"""

    # Si hay pocos resultados, agregar sugerencias
    if resultados_hibridos['total'] < 3:
        respuesta += """

### 💡 Sugerencias para mejorar la búsqueda:
• Intenta usar términos más específicos o palabras clave técnicas
• Verifica que el tipo de auditoría seleccionado sea el correcto
• Considera reformular tu pregunta usando lenguaje normativo
"""

    return respuesta

# =============================================================================
# DECORADORES Y VALIDACIÓN
# =============================================================================

def requiere_db(f):
    """Verifica que la base de datos esté cargada"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DB_AUDITORIA:
            return jsonify({"success": False, "message": "Base de datos no cargada"})
        return f(*args, **kwargs)
    return decorated

def validar_entrada(form_data):
    """Valida y sanitiza entrada del formulario"""
    errores = []

    pregunta = form_data.get("question", "").strip()
    if not pregunta or len(pregunta) < Config.MIN_QUESTION_LENGTH:
        errores.append(f"Pregunta demasiado corta (mínimo {Config.MIN_QUESTION_LENGTH} caracteres)")
    elif len(pregunta) > Config.MAX_QUESTION_LENGTH:
        errores.append(f"Pregunta demasiado larga (máximo {Config.MAX_QUESTION_LENGTH} caracteres)")

    auditoria = form_data.get("auditoria")
    if not auditoria or auditoria not in AuditoriaConfig.TIPOS:
        errores.append("Tipo de auditoría inválido")

    ente = form_data.get("ente", "").strip()

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "pregunta": text_processor.limpiar_texto(pregunta),
        "auditoria": auditoria,
        "ente": text_processor.limpiar_texto(ente) if ente else "No especificado"
    }

# =============================================================================
# RUTAS DE LA APLICACIÓN
# =============================================================================

@app.route("/", methods=["GET"])
def index():
    """Página principal"""
    chat_history = session.get("chat_history", [])
    return render_template(
        "index.html",
        chat_history=chat_history,
        auditorias_config=AuditoriaConfig.TIPOS,
        estadisticas=ESTADISTICAS_DB
    )

@app.route("/ask", methods=["POST"])
@requiere_db
def ask():
    """Endpoint principal para consultas"""
    inicio = time.time()

    try:
        # Validar entrada
        validacion = validar_entrada(request.form)
        if not validacion["valido"]:
            return jsonify({
                "success": False,
                "message": "; ".join(validacion["errores"])
            }), 400

        pregunta = validacion["pregunta"]
        auditoria_tipo = validacion["auditoria"]
        ente_tipo = validacion["ente"]

        # Verificar si usar web scraping (parámetro opcional)
        usar_web = request.form.get("usar_web_scraping", "true").lower() == "true"

        logger.info(f"📨 Consulta: {pregunta[:50]}... | Auditoría: {auditoria_tipo} | Web: {usar_web}")

        # Búsqueda híbrida
        resultados = buscar_hibrido(pregunta, auditoria_tipo, usar_web_scraping=usar_web)

        # Generar respuesta
        respuesta = generar_respuesta_completa(pregunta, auditoria_tipo, ente_tipo, resultados)

        # Guardar en historial
        chat_history = session.get("chat_history", [])
        chat_history.append({
            "question": pregunta,
            "answer": respuesta,
            "auditoria": auditoria_tipo,
            "ente": ente_tipo,
            "timestamp": datetime.now().isoformat(),
            "total_resultados": resultados['total'],
            "resultados_web": len(resultados['web'])
        })

        # Limitar historial
        if len(chat_history) > Config.CHAT_HISTORY_LIMIT:
            chat_history = chat_history[-Config.CHAT_HISTORY_LIMIT:]

        session["chat_history"] = chat_history
        session.modified = True

        tiempo_total = time.time() - inicio
        logger.info(f"✅ Consulta completada en {tiempo_total:.2f}s")

        return jsonify({
            "success": True,
            "answer": respuesta,
            "tiempo_procesamiento": f"{tiempo_total:.2f}s",
            "estadisticas": {
                "total": resultados['total'],
                "locales": len(resultados['locales']),
                "web": len(resultados['web']),
                "fuentes_web": resultados['fuentes_web']
            }
        })

    except Exception as e:
        logger.error(f"❌ Error en /ask: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Error procesando consulta"
        }), 500

@app.route("/clear", methods=["POST"])
def clear():
    """Limpiar sesión"""
    session.clear()
    flash("Nueva sesión iniciada", "success")
    return redirect(url_for("index"))

@app.route("/health", methods=["GET"])
def health():
    """Estado del sistema"""
    return jsonify({
        "status": "healthy",
        "databases_loaded": len(DB_AUDITORIA),
        "scrapers_disponibles": list(scraper_manager.scrapers.keys()),
        "cache_stats": cache_manager.estadisticas(),
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    })

@app.route("/cache/stats", methods=["GET"])
def cache_stats():
    """Estadísticas de caché"""
    return jsonify(cache_manager.estadisticas())

@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Limpiar caché"""
    try:
        cache_manager.limpiar_todo()
        return jsonify({"success": True, "message": "Caché limpiado"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/scraping/test", methods=["POST"])
def test_scraping():
    """Endpoint para probar web scraping"""
    query = request.form.get("query", "obras públicas")
    fuente = request.form.get("fuente", "all")

    try:
        if fuente == "all":
            resultado = scraper_manager.buscar_en_todos(query, max_resultados_por_fuente=2)
            return jsonify({
                "success": True,
                "query": query,
                "resultados": len(resultado.normativas),
                "fuentes": resultado.fuentes_consultadas,
                "tiempo": resultado.tiempo_busqueda,
                "datos": [n.to_dict() for n in resultado.normativas]
            })
        else:
            normativas = scraper_manager.buscar_en_fuente(fuente, query, max_resultados=3)
            return jsonify({
                "success": True,
                "query": query,
                "fuente": fuente,
                "resultados": len(normativas),
                "datos": [n.to_dict() for n in normativas]
            })
    except Exception as e:
        logger.error(f"Error en test de scraping: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# =============================================================================
# MANEJO DE ERRORES
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error 500: {error}")
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500

# =============================================================================
# INICIALIZACIÓN
# =============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("✅ Auditel v3.0 - Sistema Inteligente de Análisis Normativo")
    logger.info("=" * 80)
    logger.info(f"📊 Bases de datos cargadas: {list(DB_AUDITORIA.keys())}")
    logger.info(f"🔍 Motor local: {len(motor_busqueda_local.metadatos)} documentos")
    logger.info(f"🌐 Scrapers disponibles: {list(scraper_manager.scrapers.keys())}")
    logger.info(f"💾 Caché: {cache_manager.estadisticas()}")
    logger.info("=" * 80)

    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5020, debug=debug_mode)
