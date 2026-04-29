import os
import json
import re
import logging
import hashlib
import requests
import unicodedata
from html import escape
from datetime import datetime, timedelta
from functools import wraps
from logging.handlers import RotatingFileHandler

import heapq
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv

# Cargar variables de entorno ANTES de Config para que os.getenv() las encuentre
load_dotenv()

from config import PORT
from scripts.utils import AUDITORIA_DATA
from scripts.auth import (
    authenticate,
    get_authorized_users,
    get_canonical_username,
    get_user_display_name,
    is_authenticated,
    login_required,
)

# =============================================================================
# CONFIGURACIÓN MEJORADA DE LOGGING
# =============================================================================

def configurar_logging_detallado():
    """Configura logging más detallado y estructurado"""

    # Ensure log directory exists
    from pathlib import Path
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s | [%(filename)s:%(lineno)d]'
    )

    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
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
    
    # Evitar log excesivo de librerías externas
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sklearn').setLevel(logging.WARNING)
    
    return logger

logger = configurar_logging_detallado()

# =============================================================================
# CONFIGURACIÓN CENTRALIZADA
# =============================================================================

class Config:
    """Configuración centralizada de la aplicación"""
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TIMEOUT = 60 * 60  # 1 hora en segundos
    
    # Límites
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    MAX_QUESTION_LENGTH = 2000
    MIN_QUESTION_LENGTH = 3
    
    # Rendimiento
    CACHE_SIZE = 100
    SEARCH_RESULTS_LIMIT = 8
    CHAT_HISTORY_LIMIT = 10
    
    # Motor de búsqueda
    TFIDF_MAX_FEATURES = 5000
    SIMILARITY_THRESHOLD = 0.1
    TOP_N_RESULTS = 3


AUTO_AUDITORIA = "auto"
AUTO_AUDITORIA_LABEL = "Base unificada"


PALABRAS_GENERICAS_CONSULTA = {
    "aplica", "aplican", "aplicable", "aplicables", "articulo", "articulos",
    "consulta", "consulta", "cual", "cuales", "cuales", "como", "dame",
    "debe", "debo", "del", "donde", "ejercicio", "ley", "leyes", "mexico",
    "norma", "normas", "normativa", "normativas", "normatividad",
    "publico", "publicos", "quiero", "que", "quieres", "relacionada",
    "relacionado", "sobre", "tema", "tipo",
}

PALABRAS_GENERICAS_POR_AUDITORIA = {
    "Obra Pública": {"obra", "obras", "publica", "publicas"},
    "Financiera": {"financiera", "financiero", "financieras", "financieros"},
}


def obtener_chatbot_config():
    """Expone el estado público de la integración futura del chatbot."""
    provider = (os.getenv("CHAT_PROVIDER") or "qwen").strip().lower() or "qwen"
    provider_label = "Qwen Chat" if provider == "qwen" else provider.replace("_", " ").title()
    qwen_api_key = (os.getenv("QWEN_API_KEY") or "").strip()
    qwen_model = (os.getenv("QWEN_MODEL") or "").strip()
    qwen_ready = bool(qwen_api_key)

    if qwen_ready:
        status_copy = (
            "La configuración base ya fue detectada. La interfaz puede conectarse al proveedor cuando se implemente el backend."
        )
    else:
        status_copy = (
            "La interfaz ya quedó preparada para Qwen. Solo falta agregar la API key cuando termines de crear la cuenta."
        )

    return {
        "provider": provider,
        "provider_label": provider_label,
        "qwen_ready": qwen_ready,
        "qwen_model": qwen_model,
        "status_copy": status_copy,
        "default_auditoria": AUTO_AUDITORIA,
        "default_ente": "No aplica",
        "bot_name": "Chatbot",
        "slash_commands": [
            {
                "value": AUTO_AUDITORIA,
                "label": AUTO_AUDITORIA_LABEL,
                "description": "Consulta simultánea en todas las bases disponibles.",
            },
            {
                "value": "Obra Pública",
                "label": "Obra Pública",
                "description": "Normativa de obra, contratación y licitaciones.",
            },
            {
                "value": "Financiera",
                "label": "Financiero",
                "description": "Normativa contable, presupuestal y de control financiero.",
            },
        ],
    }


CHATBOT_CONFIG = obtener_chatbot_config()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.permanent_session_lifetime = timedelta(seconds=Config.SESSION_TIMEOUT)

# Configuración de Flask
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# =============================================================================
# SISTEMA DE CACHÉ MEJORADO
# =============================================================================

class SistemaCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def _generar_clave(self, consulta, auditoria_tipo):
        """Genera clave única para la consulta"""
        contenido = f"{consulta}_{auditoria_tipo}".encode('utf-8')
        return hashlib.md5(contenido).hexdigest()
    
    def obtener(self, consulta, auditoria_tipo):
        clave = self._generar_clave(consulta, auditoria_tipo)
        if clave in self.cache:
            # Mover al final (más reciente)
            if clave in self.access_order:
                self.access_order.remove(clave)
            self.access_order.append(clave)
            return self.cache[clave]
        return None
    
    def guardar(self, consulta, auditoria_tipo, resultado):
        clave = self._generar_clave(consulta, auditoria_tipo)
        
        # Gestionar tamaño máximo
        if len(self.cache) >= self.max_size and self.access_order:
            clave_mas_antigua = self.access_order.pop(0)
            del self.cache[clave_mas_antigua]
        
        self.cache[clave] = resultado
        self.access_order.append(clave)
        
    def estadisticas(self):
        return {
            'tamaño_actual': len(self.cache),
            'tamaño_maximo': self.max_size,
            'claves': list(self.cache.keys())[:5]  # Primeras 5 claves como muestra
        }

# =============================================================================
# SISTEMA DE MONITOREO DE RENDIMIENTO
# =============================================================================

class MonitorRendimiento:
    def __init__(self):
        self.metricas = {
            'solicitudes_totales': 0,
            'solicitudes_exitosas': 0,
            'solicitudes_fallidas': 0,
            'tiempo_respuesta_promedio': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errores_por_tipo': {}
        }
        self.tiempos_solicitud = []
    
    def registrar_solicitud(self, exitosa, tiempo_procesamiento):
        self.metricas['solicitudes_totales'] += 1
        if exitosa:
            self.metricas['solicitudes_exitosas'] += 1
        else:
            self.metricas['solicitudes_fallidas'] += 1
        
        self.tiempos_solicitud.append(tiempo_procesamiento)
        # Mantener solo últimos 100 registros
        if len(self.tiempos_solicitud) > 100:
            self.tiempos_solicitud.pop(0)
        
        if self.tiempos_solicitud:
            self.metricas['tiempo_respuesta_promedio'] = sum(self.tiempos_solicitud) / len(self.tiempos_solicitud)
    
    def registrar_cache_hit(self):
        self.metricas['cache_hits'] += 1
    
    def registrar_cache_miss(self):
        self.metricas['cache_misses'] += 1
    
    def registrar_error(self, tipo_error):
        if tipo_error not in self.metricas['errores_por_tipo']:
            self.metricas['errores_por_tipo'][tipo_error] = 0
        self.metricas['errores_por_tipo'][tipo_error] += 1
    
    def obtener_metricas(self):
        return self.metricas.copy()

# =============================================================================
# CONFIGURACIÓN DE AUDITORÍAS
# =============================================================================

# Configuración de auditorías
AUDITORIA_CONFIG = {
    "Obra Pública": {
        "archivo": "obra_publica.json",
        "descripcion": "Análisis de normativas de construcción, licitaciones y contratación pública",
        "campos_normativas": [
            "normatividad_local_administracion_directa",
            "normatividad_local_contrato",
            "normatividad_federal_administracion_directa",
            "normatividad_federal_contratacion"
        ]
    },
    "Financiera": {
        "archivo": "financiero.json",
        "descripcion": "Análisis de normativas contables, presupuestales y de control financiero",
        "campos_normativas": [
            "normatividad_local",
            "normatividad_federal"
        ]
    }
}

DB_AUDITORIA = {}
ESTADISTICAS_DB = {}

# =============================================================================
# CARGA OPTIMIZADA DE BASES DE DATOS
# =============================================================================

def cargar_bases_datos():
    """Carga todas las bases de datos de auditorías de forma optimizada"""
    bases_cargadas = {}
    estadisticas = {}

    for auditoria_nombre, config in AUDITORIA_CONFIG.items():
        try:
            datos = AUDITORIA_DATA.get(auditoria_nombre)
            if datos is None:
                logger.error(f"❌ Archivo no encontrado: {config['archivo']}")
                continue

            # Validar estructura básica
            if not isinstance(datos, list):
                logger.error(f"❌ Estructura inválida en {config['archivo']}: se esperaba lista")
                continue

            bases_cargadas[auditoria_nombre] = datos

            # Estadísticas detalladas
            estadisticas[auditoria_nombre] = {
                'registros': len(datos),
                'campos_normativas': config["campos_normativas"],
                'descripcion': config["descripcion"],
                'campos_por_registro': len(datos[0].keys()) if datos else 0
            }

            logger.info(f"✅ {auditoria_nombre}: {len(datos)} registros - {config['descripcion']}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error JSON en {config['archivo']}: {e}")
        except Exception as e:
            logger.error(f"❌ Error al leer {config['archivo']}: {e}")

    logger.info(f"📊 Resumen carga: {len(bases_cargadas)} auditorías cargadas")
    return bases_cargadas, estadisticas

# Cargar bases de datos al inicio
DB_AUDITORIA, ESTADISTICAS_DB = cargar_bases_datos()

# =============================================================================
# MOTOR DE BÚSQUEDA SEMÁNTICA MEJORADO
# =============================================================================

class MotorBusquedaNormativasMejorado:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=['el', 'la', 'de', 'en', 'y', 'o', 'un', 'una', 'es', 'son'],
            min_df=1,
            max_df=0.9,
            max_features=Config.TFIDF_MAX_FEATURES
        )
        self.matriz_tfidf_unificada = None
        self.metadatos_unificados = []
        self._inicializado = False
        
        self._preparar_datos_unificados()

    def _preparar_datos_unificados(self):
        """Prepara todos los datos en un solo corpus para mejor consistencia"""
        todos_documentos = []
        self.metadatos_unificados = []
        
        for auditoria, datos in DB_AUDITORIA.items():
            for idx, item in enumerate(datos):
                texto_documento = self._crear_documento_texto(item)
                todos_documentos.append(texto_documento)
                self.metadatos_unificados.append({
                    'indice': len(todos_documentos) - 1,
                    'auditoria': auditoria,
                    'item': item,
                    'tipo': item.get('tipo', ''),
                    'descripcion': item.get('descripcion_irregularidad', '')
                })
        
        if todos_documentos:
            try:
                self.matriz_tfidf_unificada = self.vectorizer.fit_transform(todos_documentos)
                self._inicializado = True
                logger.info(f"✅ Motor unificado preparado: {len(todos_documentos)} documentos totales")
            except Exception as e:
                logger.error(f"❌ Error preparando motor unificado: {e}")
                self._inicializado = False
        else:
            logger.warning("⚠️ No hay documentos para preparar el motor de búsqueda")
            self._inicializado = False

    def _crear_documento_texto(self, item):
        """Crea un documento de texto para búsqueda desde un ítem"""
        campos = [
            item.get('tipo', ''),
            item.get('concepto', ''),
            item.get('descripcion_irregularidad', ''),
            item.get('categoria', ''),
            item.get('subcategoria', '')
        ]

        # Agregar normativas
        for key in item.keys():
            if 'normatividad' in key.lower() and item[key]:
                campos.append(str(item[key]))

        return ' '.join(filter(None, campos))

    def esta_inicializado(self):
        """Verifica si el motor está correctamente inicializado"""
        return self._inicializado and self.matriz_tfidf_unificada is not None

    def buscar_semanticamente(self, consulta, auditoria_tipo, top_n=5):
        """Busca normativas usando similitud semántica en el corpus unificado"""
        if not self.esta_inicializado():
            logger.warning("⚠️ Motor de búsqueda no inicializado")
            return []

        try:
            # Transformar consulta
            consulta_tfidf = self.vectorizer.transform([consulta])
            
            # Calcular similitudes con todo el corpus
            similitudes = cosine_similarity(consulta_tfidf, self.matriz_tfidf_unificada).flatten()

            # Filtrar por auditoría y obtener top N resultados
            indices_relevantes = []
            busqueda_unificada = es_busqueda_unificada(auditoria_tipo)
            for idx, similitud in enumerate(similitudes):
                if (
                    similitud > Config.SIMILARITY_THRESHOLD and
                    (
                        busqueda_unificada or
                        self.metadatos_unificados[idx]['auditoria'] == auditoria_tipo
                    )
                ):
                    indices_relevantes.append((idx, similitud))

            # Ordenar por similitud y tomar top N
            indices_relevantes.sort(key=lambda x: x[1], reverse=True)
            indices_top = indices_relevantes[:top_n]

            resultados = []
            for idx, similitud in indices_top:
                metadato = self.metadatos_unificados[idx]
                resultados.append({
                    'item': metadato['item'],
                    'similitud': float(similitud),
                    'indice': idx,
                    'auditoria': metadato['auditoria']
                })

            return resultados

        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {e}")
            return []

# =============================================================================
# INICIALIZACIÓN DE COMPONENTES GLOBALES
# =============================================================================

# Inicializar componentes
motor_busqueda = MotorBusquedaNormativasMejorado()
cache_busqueda = SistemaCache(max_size=Config.CACHE_SIZE)
monitor_rendimiento = MonitorRendimiento()

# =============================================================================
# FUNCIONES AUXILIARES MEJORADAS
# =============================================================================

def sanitizar_texto(texto, max_length=2000):
    """Sanitiza texto eliminando caracteres peligrosos"""
    if not texto:
        return ""

    # Eliminar caracteres de control y espacios extra
    texto = re.sub(r'[\x00-\x1F\x7F]', '', texto.strip())
    texto = re.sub(r'\s+', ' ', texto)  # Normalizar espacios

    # Limitar longitud
    return texto[:max_length]

def validar_auditoria_tipo(tipo):
    """Valida que el tipo de auditoría sea válido"""
    tipo_normalizado = (tipo or AUTO_AUDITORIA).strip()
    if tipo_normalizado == AUTO_AUDITORIA:
        return AUTO_AUDITORIA
    return tipo_normalizado if tipo_normalizado in AUDITORIA_CONFIG else None


def es_busqueda_unificada(auditoria_tipo):
    """Indica si la consulta debe buscar en toda la base."""
    return auditoria_tipo == AUTO_AUDITORIA


def obtener_etiqueta_auditoria(auditoria_tipo):
    """Devuelve una etiqueta legible para UI e historial."""
    if es_busqueda_unificada(auditoria_tipo):
        return AUTO_AUDITORIA_LABEL
    return auditoria_tipo

def validar_y_sanitizar_entrada(datos_form):
    """Valida y sanitiza todas las entradas del formulario"""
    errores = []
    
    # Validar pregunta
    pregunta = datos_form.get("question", "").strip()
    if not pregunta:
        errores.append("La pregunta no puede estar vacía")
    elif len(pregunta) < Config.MIN_QUESTION_LENGTH:
        errores.append(f"La pregunta debe tener al menos {Config.MIN_QUESTION_LENGTH} caracteres")
    elif len(pregunta) > Config.MAX_QUESTION_LENGTH:
        errores.append(f"La pregunta es demasiado larga (máximo {Config.MAX_QUESTION_LENGTH} caracteres)")
    
    # Validar tipo de auditoría
    auditoria_tipo = validar_auditoria_tipo(datos_form.get("auditoria"))
    if not auditoria_tipo:
        errores.append("Tipo de auditoría inválido")
    
    # Validar ente (opcional)
    ente_tipo = datos_form.get("ente", "").strip()
    if ente_tipo and len(ente_tipo) > 100:
        errores.append("El tipo de ente es demasiado largo")
    
    # Sanitizar
    pregunta_sanitizada = sanitizar_texto(pregunta)
    ente_sanitizado = sanitizar_texto(ente_tipo, max_length=100) if ente_tipo else "No especificado"
    
    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "pregunta": pregunta_sanitizada,
        "auditoria": auditoria_tipo,
        "ente": ente_sanitizado
    }

# =============================================================================
# DECORADORES MEJORADOS
# =============================================================================

def requiere_configuracion(f):
    """Decorator para verificar configuración inicial"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not DB_AUDITORIA:
            return jsonify({"success": False, "message": "Bases de datos no cargadas correctamente."})
        return f(*args, **kwargs)
    return decorated_function

def requiere_auditoria(f):
    """Decorator para verificar que la auditoría existe"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auditoria_tipo = request.form.get("auditoria")
        if not validar_auditoria_tipo(auditoria_tipo):
            return jsonify({"success": False, "message": "Tipo de auditoría inválido o no configurado."})
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# MANEJO DE SESIÓN MEJORADO
# =============================================================================

def get_chat_history():
    """Obtiene el historial de chat con validación"""
    historial = session.get("chat_history", [])
    # Validar que cada mensaje tenga la estructura correcta
    historial_valido = []
    for msg in historial:
        if (isinstance(msg, dict) and 
            'question' in msg and 
            'answer' in msg and 
            'timestamp' in msg):
            historial_valido.append(msg)
    return historial_valido

def set_chat_history(history, max_mensajes=Config.CHAT_HISTORY_LIMIT):
    """Guarda el historial de chat con mejor gestión de memoria"""
    if len(history) > max_mensajes:
        # Mantener los primeros 2 mensajes (configuración) y los últimos N
        if len(history) > 2:
            history = history[:2] + history[-(max_mensajes-2):]
        else:
            history = history[-max_mensajes:]
    
    # Limpiar datos grandes si existen
    for msg in history:
        if 'answer' in msg and len(msg['answer']) > 10000:
            msg['answer'] = msg['answer'][:10000] + "... [truncado]"
    
    session["chat_history"] = history
    session.modified = True


def _safe_next_url(raw_url):
    """Valida redirecciones internas para evitar saltos externos."""
    candidate_url = str(raw_url or "").strip()
    if not candidate_url.startswith("/") or candidate_url.startswith("//"):
        return ""
    return candidate_url

# =============================================================================
# FUNCIONES DE BÚSQUEDA Y ANÁLISIS MEJORADAS
# =============================================================================

def buscar_semanticamente_con_cache(consulta, auditoria_tipo, top_n=5):
    """Búsqueda semántica con cache para mejor rendimiento"""
    
    # Verificar cache primero
    resultado_cache = cache_busqueda.obtener(consulta, auditoria_tipo)
    if resultado_cache:
        logger.info(f"✅ Cache hit para consulta: {consulta[:50]}...")
        monitor_rendimiento.registrar_cache_hit()
        return resultado_cache
    
    # Búsqueda normal
    monitor_rendimiento.registrar_cache_miss()
    resultados = motor_busqueda.buscar_semanticamente(consulta, auditoria_tipo, top_n)
    
    # Guardar en cache solo si hay resultados relevantes
    if resultados and any(r['similitud'] > 0.2 for r in resultados):
        cache_busqueda.guardar(consulta, auditoria_tipo, resultados)
    
    return resultados

def analizar_patrones_consulta(pregunta):
    """Analiza patrones en la consulta para mejorar resultados"""
    pregunta_normalizada = normalizar_texto_comparable(pregunta)

    patrones = {
        'licitacion': any(
            palabra in pregunta_normalizada
            for palabra in ['licitacion', 'convocatoria', 'adjudicacion', 'proceso selectivo']
        ),
        'contratacion': any(
            palabra in pregunta_normalizada
            for palabra in ['contratacion', 'contrato', 'convenio']
        ),
        'fiscalizacion': any(
            palabra in pregunta_normalizada
            for palabra in ['fiscalizacion', 'control', 'verificacion']
        ),
        'presupuesto': any(
            palabra in pregunta_normalizada
            for palabra in ['presupuesto', 'ejercicio', 'gasto']
        ),
        'transparencia': any(
            palabra in pregunta_normalizada
            for palabra in ['transparencia', 'acceso informacion', 'rendicion']
        ),
    }

    return {k: v for k, v in patrones.items() if v}


def normalizar_texto_comparable(texto):
    """Normaliza texto para comparaciones semánticas simples."""
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def extraer_tokens_relevantes(texto, auditoria_tipo=None):
    """Extrae términos útiles y elimina palabras demasiado genéricas."""
    texto_normalizado = normalizar_texto_comparable(texto)
    if not texto_normalizado:
        return []

    palabras_omitidas = set(PALABRAS_GENERICAS_CONSULTA)
    palabras_omitidas.update(PALABRAS_GENERICAS_POR_AUDITORIA.get(auditoria_tipo, set()))

    tokens = []
    for token in texto_normalizado.split():
        if token in palabras_omitidas:
            continue
        if len(token) <= 2 and not token.isdigit():
            continue
        tokens.append(token)

    return tokens


def preparar_consulta_busqueda(pregunta, auditoria_tipo):
    """Reduce ruido de la consulta antes de la búsqueda semántica."""
    return " ".join(extraer_tokens_relevantes(pregunta, auditoria_tipo)).strip()


def limpiar_consulta_concepto(pregunta):
    """Elimina frases comunes para aislar el concepto consultado."""
    consulta = normalizar_texto_comparable(pregunta)
    frases_comunes = [
        "cual es la normativa aplicable para",
        "cual es la normativa aplicable a",
        "cual es la normativa de",
        "cual es la normativa del",
        "cual es la normatividad de",
        "cual es la normatividad del",
        "dame la normativa de",
        "dame la normatividad de",
        "normativa aplicable para",
        "normativa aplicable a",
        "normativa de",
        "normativa del",
        "normatividad de",
        "normatividad del",
        "quiero la normativa de",
        "quiero la normatividad de",
        "sobre el concepto",
        "para el concepto",
        "del concepto",
        "concepto",
    ]

    for frase in frases_comunes:
        consulta = consulta.replace(frase, " ")

    consulta = re.sub(r"\s+", " ", consulta).strip()
    return consulta


def calcular_coincidencia_concepto(consulta, candidato):
    """Devuelve un puntaje simple de coincidencia entre consulta y concepto/tipo."""
    consulta_norm = limpiar_consulta_concepto(consulta)
    candidato_norm = normalizar_texto_comparable(candidato)

    if not consulta_norm or not candidato_norm:
        return 0

    if consulta_norm == candidato_norm:
        return 3

    if candidato_norm in consulta_norm or consulta_norm in candidato_norm:
        return 2

    tokens_consulta = set(consulta_norm.split())
    tokens_candidato = set(candidato_norm.split())
    if not tokens_consulta or not tokens_candidato:
        return 0

    cobertura = len(tokens_consulta & tokens_candidato) / len(tokens_candidato)
    return 1 if cobertura >= 0.7 else 0


def calcular_cobertura_textual(pregunta, normativa, auditoria_tipo):
    """Mide cuántos términos relevantes de la consulta están en el resultado."""
    tokens_consulta = set(extraer_tokens_relevantes(pregunta, auditoria_tipo))
    if not tokens_consulta:
        return 0.0

    texto_candidato = " ".join(filter(None, [
        normativa.get('tipo_irregularidad', ''),
        normativa.get('concepto', ''),
        normativa.get('descripcion', ''),
    ]))
    tokens_candidato = set(extraer_tokens_relevantes(texto_candidato, auditoria_tipo))
    if not tokens_candidato:
        return 0.0

    return len(tokens_consulta & tokens_candidato) / len(tokens_consulta)


def es_consulta_por_concepto(pregunta, normativas):
    """Detecta si la consulta apunta directamente a un concepto o tipo específico."""
    for normativa in normativas[:3]:
        candidatos = [
            normativa.get('concepto', ''),
            normativa.get('tipo_irregularidad', ''),
        ]
        if max(calcular_coincidencia_concepto(pregunta, candidato) for candidato in candidatos) > 0:
            return True
    return False


def filtrar_normativas_por_concepto(pregunta, normativas):
    """Reduce resultados a los conceptos que coinciden mejor con la consulta."""
    coincidencias = []

    for normativa in normativas:
        puntaje = max(
            calcular_coincidencia_concepto(pregunta, normativa.get('concepto', '')),
            calcular_coincidencia_concepto(pregunta, normativa.get('tipo_irregularidad', '')),
        )
        if puntaje > 0:
            coincidencias.append((puntaje, normativa))

    if not coincidencias:
        return normativas

    max_puntaje = max(puntaje for puntaje, _ in coincidencias)
    filtradas = [
        normativa for puntaje, normativa in coincidencias
        if puntaje == max_puntaje
    ]
    filtradas.sort(key=lambda item: item['puntaje_similitud'], reverse=True)
    return filtradas


def combinar_normativas_duplicadas(actual, candidata):
    """Combina duplicados conservando la versión más útil para la respuesta."""
    criterio_actual = (
        actual.get('puntaje_similitud', 0),
        len(actual.get('descripcion', '')),
        1 if actual.get('origen_fuente') == 'base' else 0,
        len(actual.get('concepto', '')),
    )
    criterio_candidata = (
        candidata.get('puntaje_similitud', 0),
        len(candidata.get('descripcion', '')),
        1 if candidata.get('origen_fuente') == 'base' else 0,
        len(candidata.get('concepto', '')),
    )

    preferida = actual if criterio_actual >= criterio_candidata else candidata
    secundaria = candidata if preferida is actual else actual

    combinada = preferida.copy()
    combinada['normativas'] = preferida['normativas'].copy()

    for tipo_norma, texto_norma in secundaria.get('normativas', {}).items():
        if tipo_norma not in combinada['normativas'] and texto_norma:
            combinada['normativas'][tipo_norma] = texto_norma

    if not combinada.get('descripcion') and secundaria.get('descripcion'):
        combinada['descripcion'] = secundaria['descripcion']

    if not combinada.get('concepto') and secundaria.get('concepto'):
        combinada['concepto'] = secundaria['concepto']

    combinada['puntaje_similitud'] = max(
        actual.get('puntaje_similitud', 0),
        candidata.get('puntaje_similitud', 0),
    )
    combinada['origen_fuente'] = (
        preferida.get('origen_fuente')
        if preferida.get('origen_fuente') == secundaria.get('origen_fuente')
        else 'mixta'
    )

    return combinada


def deduplicar_normativas_por_texto(normativas):
    """Elimina repeticiones cuando varias fuentes apuntan a la misma normativa."""
    normativas_unicas = {}

    for normativa in normativas:
        tipo_normalizado = normalizar_texto_comparable(normativa.get('tipo_irregularidad', ''))
        firma_normativa = tuple(
            (tipo_norma, normalizar_texto_comparable(texto_norma))
            for tipo_norma, texto_norma in sorted(normativa.get('normativas', {}).items())
        )
        clave = tipo_normalizado or firma_normativa

        if clave not in normativas_unicas:
            normativas_unicas[clave] = {
                **normativa,
                'normativas': normativa.get('normativas', {}).copy(),
            }
            continue

        normativas_unicas[clave] = combinar_normativas_duplicadas(
            normativas_unicas[clave],
            normativa,
        )

    return list(normativas_unicas.values())


def filtrar_normativas_por_confianza(pregunta, auditoria_tipo, normativas):
    """Descarta coincidencias débiles que solo comparten términos genéricos."""
    if not extraer_tokens_relevantes(pregunta, auditoria_tipo):
        return []

    filtradas = []
    for normativa in normativas:
        puntaje_textual = calcular_cobertura_textual(pregunta, normativa, auditoria_tipo)
        normativa['puntaje_textual'] = puntaje_textual
        similitud = normativa.get('puntaje_similitud', 0)

        if (
            puntaje_textual >= 0.34 or
            (puntaje_textual >= 0.20 and similitud >= 0.12) or
            similitud >= 0.28
        ):
            filtradas.append(normativa)

    filtradas.sort(
        key=lambda item: (
            item.get('puntaje_textual', 0),
            item.get('puntaje_similitud', 0),
            len(item.get('descripcion', '')),
        ),
        reverse=True,
    )
    return filtradas


def generar_sugerencias_busqueda(pregunta, auditoria_tipo, patrones):
    """Crea sugerencias compactas y útiles cuando no hay una coincidencia sólida."""
    sugerencias = []

    if es_busqueda_unificada(auditoria_tipo):
        sugerencias.extend([
            "Prueba con el hallazgo concreto o con el concepto exacto de la irregularidad.",
            "Si la consulta es de obra pública, menciona términos como conceptos pagados no ejecutados o volúmenes pagados no ejecutados.",
            "Si la consulta es financiera, intenta con expresiones como no presentan pólizas o ingresos no registrados.",
        ])
    elif auditoria_tipo == "Obra Pública":
        if any(clave in patrones for clave in ("licitacion", "contratacion")):
            sugerencias.append(
                "La base actual de Obra Pública responde mejor a irregularidades específicas que a temas generales como licitación."
            )
        sugerencias.extend([
            "Prueba con el hallazgo concreto: conceptos pagados no ejecutados, volúmenes pagados no ejecutados o precios superiores al mercado.",
            "Si buscas contratación, formula la consulta por el incumplimiento exacto observado y no solo por la etapa general.",
        ])
    else:
        sugerencias.extend([
            "Prueba con el hallazgo concreto: no presentan pólizas, saldos contrarios a su naturaleza o ingresos no registrados.",
            "Incluye el documento o incumplimiento específico para mejorar la coincidencia.",
        ])

    if not extraer_tokens_relevantes(pregunta, auditoria_tipo):
        sugerencias.insert(
            0,
            "Evita consultas demasiado generales; usa el concepto, irregularidad o incumplimiento puntual.",
        )

    return sugerencias[:3]

def extraer_normativas_relevantes(auditoria_tipo, pregunta):
    """Extrae las normativas relevantes usando búsqueda semántica mejorada con cache"""
    if not es_busqueda_unificada(auditoria_tipo) and auditoria_tipo not in DB_AUDITORIA:
        return []

    contexto_consulta = None if es_busqueda_unificada(auditoria_tipo) else auditoria_tipo
    consulta_busqueda = preparar_consulta_busqueda(pregunta, contexto_consulta)
    if not consulta_busqueda:
        return []

    # Usar motor semántico con cache
    resultados_semanticos = buscar_semanticamente_con_cache(
        consulta_busqueda,
        auditoria_tipo,
        top_n=12 if es_busqueda_unificada(auditoria_tipo) else 8,
    )

    normativas_encontradas = []

    for resultado in resultados_semanticos:
        irregularidad = resultado['item']
        similitud = resultado['similitud']
        auditoria_resultado = resultado['auditoria']

        # Extraer normativas específicas según configuración
        config_auditoria = AUDITORIA_CONFIG[auditoria_resultado]
        normativas = {}

        for campo_normativa in config_auditoria['campos_normativas']:
            if irregularidad.get(campo_normativa):
                nombre_amigable = campo_normativa.replace('_', ' ').title()
                normativas[nombre_amigable] = irregularidad[campo_normativa]

        if normativas:
            normativas_encontradas.append({
                'tipo_irregularidad': irregularidad.get('tipo', 'No especificado'),
                'concepto': irregularidad.get('concepto', ''),
                'descripcion': irregularidad.get('descripcion_irregularidad', ''),
                'normativas': normativas,
                'puntaje_similitud': similitud,
                'categoria': irregularidad.get('categoria', 'General'),
                'subcategoria': irregularidad.get('subcategoria', ''),
                'origen_fuente': irregularidad.get('origen_fuente', 'base'),
                'auditoria': auditoria_resultado,
            })

    normativas_encontradas = deduplicar_normativas_por_texto(normativas_encontradas)
    normativas_encontradas = filtrar_normativas_por_confianza(
        pregunta,
        contexto_consulta,
        normativas_encontradas,
    )
    return normativas_encontradas[:Config.TOP_N_RESULTS]

def generar_enlaces_busqueda_internet(pregunta, auditoria_tipo):
    """Genera enlaces de búsqueda en internet para normativas"""
    try:
        consulta_codificada = requests.utils.quote(f"{pregunta} {auditoria_tipo} normativa México")

        enlaces = {
            "Diario Oficial de la Federación": f"https://www.dof.gob.mx/busqueda_avanzada.php?q={consulta_codificada}",
            "Cámara de Diputados": "http://www.diputados.gob.mx/LeyesBiblio/index.htm",
            "Suprema Corte de Justicia": f"https://www.scjn.gob.mx/busqueda?search={consulta_codificada}",
            "Búsqueda en Google": f"https://www.google.com/search?q={consulta_codificada}"
        }

        seccion_busqueda = "\n\n## 🔍 Búsquedas Sugeridas en Internet\n\n"
        seccion_busqueda += "Para información más actualizada, puedes consultar estas fuentes oficiales:\n\n"

        for nombre, url in enlaces.items():
            seccion_busqueda += f"- [{nombre}]({url})\n"

        seccion_busqueda += "\n*💡 Estos enlaces te llevarán a fuentes oficiales para verificar la normativa más actualizada*"

        return seccion_busqueda
    except Exception as e:
        logger.error(f"Error generando enlaces de búsqueda: {e}")
        return ""

def generar_analisis_normativo(pregunta, auditoria_tipo, ente_tipo=None):
    """Genera un análisis normativo completo basado en la pregunta"""
    # Analizar patrones de la consulta
    patrones = analizar_patrones_consulta(pregunta)

    # Extraer normativas relevantes
    normativas = extraer_normativas_relevantes(auditoria_tipo, pregunta)
    consulta_por_concepto = es_consulta_por_concepto(pregunta, normativas)
    etiqueta_auditoria = obtener_etiqueta_auditoria(auditoria_tipo)

    if consulta_por_concepto:
        normativas = filtrar_normativas_por_concepto(pregunta, normativas)
        normativas = deduplicar_normativas_por_texto(normativas)

    if not normativas:
        sugerencias = generar_sugerencias_busqueda(pregunta, auditoria_tipo, patrones)
        mensaje = "No encontré una coincidencia suficientemente precisa en la base actual."

        if es_busqueda_unificada(auditoria_tipo):
            mensaje = "No encontré una coincidencia suficientemente precisa en la base unificada."

        if auditoria_tipo == "Obra Pública" and any(
            clave in patrones for clave in ("licitacion", "contratacion")
        ):
            mensaje = "No encontré una coincidencia específica para licitación o contratación en la base actual."

        return {
            "encontrado": False,
            "mensaje": mensaje,
            "sugerencias": sugerencias,
            "patrones_detectados": patrones,
            "normativas": []
        }

    # Construir respuesta estructurada mejorada
    auditorias_consultadas = sorted({
        normativa.get("auditoria")
        for normativa in normativas
        if normativa.get("auditoria")
    })

    analisis = {
        "encontrado": True,
        "resumen": (
            "Se encontró 1 coincidencia relevante para tu consulta."
            if len(normativas) == 1
            else f"Se encontraron {len(normativas)} coincidencias relevantes para tu consulta."
        ),
        "normativas": normativas,
        "tipo_auditoria": etiqueta_auditoria,
        "ente_tipo": ente_tipo,
        "solo_normativa": consulta_por_concepto,
        "patrones_detectados": patrones,
        "auditorias_consultadas": auditorias_consultadas,
        "estadisticas": {
            "total_encontrado": len(normativas),
            "max_similitud": max(n['puntaje_similitud'] for n in normativas) if normativas else 0,
            "categorias_unicas": len(set(n['categoria'] for n in normativas))
        }
    }

    return analisis

def formatear_respuesta_normativa(analisis):
    """Formatea la respuesta normativa con una salida compacta y clara."""
    if not analisis["encontrado"]:
        sugerencias_html = "".join(
            f"<li>{escape(sugerencia)}</li>"
            for sugerencia in analisis["sugerencias"]
        )
        return f"""
<div class="analysis-response">
  <div class="analysis-summary">
    <p class="analysis-kicker">Sin coincidencia precisa</p>
    <p>{escape(analisis["mensaje"])}</p>
  </div>
  <div class="analysis-help">
    <p><strong>Prueba con:</strong></p>
    <ul>{sugerencias_html}</ul>
  </div>
</div>
""".strip()

    if analisis.get("solo_normativa"):
        encabezado = "Normativa aplicable"
        subtitulo = "Encontré una coincidencia directa con el concepto consultado."
    else:
        encabezado = "Resultado"
        subtitulo = analisis["resumen"]

    bloques = [
        '<div class="analysis-response">',
        '  <div class="analysis-summary">',
        f'    <p class="analysis-kicker">{escape(encabezado)}</p>',
        f'    <p>{escape(subtitulo)}</p>',
        '  </div>',
    ]

    for i, normativa in enumerate(analisis["normativas"], 1):
        bloques.append(formatear_normativa_individual(
            normativa,
            i,
            solo_normativa=analisis.get("solo_normativa", False),
        ))

    bloques.append('</div>')
    return "\n".join(bloques)


def formatear_texto_html(texto):
    """Escapa texto y respeta saltos de línea básicos."""
    texto_limpio = (texto or "").strip()
    if not texto_limpio:
        return ""

    lineas = [escape(linea.strip()) for linea in texto_limpio.splitlines() if linea.strip()]
    return "<br>".join(lineas)


def obtener_etiqueta_relevancia(normativa):
    """Devuelve una etiqueta visual corta para la coincidencia."""
    puntaje_textual = normativa.get('puntaje_textual', 0)
    similitud = normativa.get('puntaje_similitud', 0)

    if puntaje_textual >= 0.75 or similitud >= 0.45:
        return "Coincidencia alta", "high"
    if puntaje_textual >= 0.34 or similitud >= 0.20:
        return "Coincidencia media", "medium"
    return "Coincidencia baja", "low"

def formatear_normativa_individual(normativa, numero, solo_normativa=False):
    """Formatea una normativa individual"""
    auditoria_html = (
        f'<p class="analysis-meta">{escape(normativa["auditoria"])}</p>'
        if normativa.get("auditoria")
        else ""
    )

    if solo_normativa:
        encabezado = f"{numero}. Normativa aplicable"
        insignia = ""
        descripcion_html = ""
        clase_extra = " compact"
    else:
        etiqueta, clase_etiqueta = obtener_etiqueta_relevancia(normativa)
        encabezado = f"{numero}. {escape(normativa['tipo_irregularidad'])}"
        insignia = f'<span class="analysis-badge {clase_etiqueta}">{etiqueta}</span>'
        descripcion_html = formatear_texto_html(normativa.get('descripcion'))
        descripcion_html = (
            f'<p class="analysis-description">{descripcion_html}</p>'
            if descripcion_html else ''
        )
        clase_extra = ""

    normativas_html = "".join(
        f'<p><strong>{escape(tipo_norma)}:</strong> {formatear_texto_html(texto_norma)}</p>'
        for tipo_norma, texto_norma in normativa['normativas'].items()
        if texto_norma
    )

    return f"""
  <section class="analysis-result{clase_extra}">
    <div class="analysis-result-head">
      <h4>{encabezado}</h4>
      {insignia}
    </div>
    {auditoria_html}
    {descripcion_html}
    <div class="analysis-norms">
      {normativas_html}
    </div>
  </section>
""".strip()

# =============================================================================
# FILTROS JINJA2 PERSONALIZADOS
# =============================================================================

def datetimeformat(value, format='%H:%M'):
    """Filtro para formatear fechas en las plantillas"""
    if not value:
        return ''
    try:
        # Si es string, convertir a datetime
        if isinstance(value, str):
            # Intentar diferentes formatos de fecha
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue

        # Si ya es datetime, formatear
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y %H:%M')

        return str(value)
    except Exception as e:
        logger.warning(f"Error formateando fecha {value}: {e}")
        return str(value)

def sum_attribute(sequence, attribute):
    """Filtro para sumar atributos de una secuencia"""
    return sum(item.get(attribute, 0) for item in sequence)

# Registrar filtros en la app
app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['sum_attribute'] = sum_attribute

# =============================================================================
# RUTAS PRINCIPALES MEJORADAS
# =============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Pantalla de acceso institucional."""
    next_url = _safe_next_url(request.values.get("next"))

    if is_authenticated():
        return redirect(next_url or url_for("index"))

    usuarios_activos = get_authorized_users()
    error = None
    selected_username = ""
    selected_display = "usuario"

    if len(usuarios_activos) == 1 and request.method == "GET":
        selected_username = usuarios_activos[0]["username"]
        selected_display = usuarios_activos[0]["display_name"]

    if request.method == "POST":
        selected_username = (request.form.get("username") or "").strip()
        selected_display = get_user_display_name(selected_username, fallback="usuario")
        password = request.form.get("password", "")

        if not usuarios_activos:
            error = "No hay usuarios activos configurados."
        elif not selected_username:
            error = "Seleccione un usuario para continuar."
        elif not authenticate(selected_username, password):
            error = "Usuario o contraseña incorrectos."
        else:
            canonical_username = get_canonical_username(selected_username) or selected_username
            session.clear()
            session.permanent = True
            session["usuario"] = canonical_username
            session["auth_user"] = canonical_username
            session["display_name"] = get_user_display_name(
                canonical_username,
                fallback=canonical_username,
            )
            return redirect(next_url or url_for("index"))

    return render_template(
        "login.html",
        error=error,
        usuarios_activos=usuarios_activos,
        selected_username=selected_username,
        selected_display=selected_display,
        next_url=next_url,
    )


@app.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión institucional activa."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
def index():
    """Página principal con datos mejorados"""
    chat_history = get_chat_history()
    return render_template(
        "index.html",
        chat_history=chat_history,
        estadisticas=ESTADISTICAS_DB,
        chatbot_config=CHATBOT_CONFIG,
    )

@app.route("/ask", methods=["POST"])
@login_required
@requiere_configuracion
@requiere_auditoria
def ask():
    """Endpoint principal para análisis normativo mejorado"""
    start_time = datetime.now()

    try:
        # Validar y sanitizar entradas mejorado
        validacion = validar_y_sanitizar_entrada(request.form)
        if not validacion["valido"]:
            monitor_rendimiento.registrar_error("validacion_entrada")
            return jsonify({
                "success": False,
                "message": "Errores de validación: " + "; ".join(validacion["errores"])
            }), 400

        question = validacion["pregunta"]
        auditoria_tipo = validacion["auditoria"]
        ente_tipo = validacion["ente"]
        auditoria_label = obtener_etiqueta_auditoria(auditoria_tipo)

        # Log de auditoría mejorado
        logger.info(f"📨 Consulta normativa - Auditoría: {auditoria_label}, Ente: {ente_tipo}, Longitud: {len(question)}")

        # GENERAR ANÁLISIS NORMATIVO MEJORADO
        analisis = generar_analisis_normativo(question, auditoria_tipo, ente_tipo)
        answer = formatear_respuesta_normativa(analisis)

        # Guardar en historial mejorado
        chat_history = get_chat_history()
        nuevo_chat = {
            "question": question,
            "answer": answer,
            "auditoria": auditoria_label,
            "ente": ente_tipo,
            "timestamp": datetime.now().isoformat(),
            "normativas_encontradas": len(analisis['normativas']) if analisis['encontrado'] else 0
        }

        chat_history.append(nuevo_chat)
        set_chat_history(chat_history)

        # Log de resultados
        tiempo_procesamiento = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Análisis completado en {tiempo_procesamiento:.2f}s - Normativas: {len(analisis['normativas']) if analisis['encontrado'] else 0}")

        # Registrar métricas de éxito
        monitor_rendimiento.registrar_solicitud(True, tiempo_procesamiento)

        return jsonify({
            "success": True,
            "answer": answer,
            "auditoria_label": auditoria_label,
            "auditorias_consultadas": analisis.get("auditorias_consultadas", []),
            "normativas_encontradas": len(analisis['normativas']) if analisis['encontrado'] else 0,
            "tiempo_procesamiento": f"{tiempo_procesamiento:.2f}s",
            "estadisticas": analisis.get("estadisticas", {})
        })

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error JSON en /ask: {e}")
        monitor_rendimiento.registrar_error("json_decode")
        monitor_rendimiento.registrar_solicitud(False, 0)
        return jsonify({
            "success": False,
            "message": "Error en el formato de datos. Verifica la entrada."
        }), 400
        
    except requests.RequestException as e:
        logger.error(f"❌ Error de conexión en /ask: {e}")
        monitor_rendimiento.registrar_error("request_exception")
        monitor_rendimiento.registrar_solicitud(False, 0)
        return jsonify({
            "success": False,
            "message": "Error de conexión. Verifica tu internet e intenta nuevamente."
        }), 503
        
    except MemoryError as e:
        logger.error(f"❌ Error de memoria en /ask: {e}")
        monitor_rendimiento.registrar_error("memory_error")
        monitor_rendimiento.registrar_solicitud(False, 0)
        return jsonify({
            "success": False,
            "message": "Error del sistema. Por favor, intenta con una consulta más pequeña."
        }), 500
        
    except Exception as e:
        logger.error(f"❌ Error inesperado en /ask: {e}", exc_info=True)
        monitor_rendimiento.registrar_error("exception_generica")
        monitor_rendimiento.registrar_solicitud(False, 0)
        return jsonify({
            "success": False,
            "message": "Error interno del servidor. Por favor, intenta nuevamente."
        }), 500

@app.route("/clear", methods=["POST"])
@login_required
def clear():
    """Limpiar la sesión y comenzar de nuevo"""
    try:
        session.pop("chat_history", None)
        session.modified = True
        flash("🔄 Nueva sesión iniciada.", "success")
        logger.info("✅ Sesión limpiada correctamente")
    except Exception as e:
        logger.error(f"Error al limpiar sesión: {e}")
        flash("⚠️ Error al limpiar la sesión", "error")

    return redirect(url_for("index"))

@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud mejorado para monitoreo"""
    status = {
        "status": "healthy" if DB_AUDITORIA else "degraded",
        "databases_loaded": len(DB_AUDITORIA),
        "total_records": sum(len(db) for db in DB_AUDITORIA.values()),
        "auditorias_activas": list(DB_AUDITORIA.keys()),
        "motor_busqueda_activo": motor_busqueda.esta_inicializado(),
        "cache_estadisticas": cache_busqueda.estadisticas(),
        "metricas_rendimiento": monitor_rendimiento.obtener_metricas(),
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }
    return jsonify(status)

@app.route("/config", methods=["GET"])
@login_required
def get_config():
    """Endpoint para obtener configuración (útil para frontend)"""
    return jsonify({
        "auditorias": AUDITORIA_CONFIG,
        "estadisticas": ESTADISTICAS_DB,
        "chatbot": {
            "provider": CHATBOT_CONFIG["provider"],
            "provider_label": CHATBOT_CONFIG["provider_label"],
            "qwen_ready": CHATBOT_CONFIG["qwen_ready"],
            "qwen_model": CHATBOT_CONFIG["qwen_model"],
            "default_auditoria": CHATBOT_CONFIG["default_auditoria"],
            "default_ente": CHATBOT_CONFIG["default_ente"],
        },
        "limites": {
            "max_question_length": Config.MAX_QUESTION_LENGTH,
            "min_question_length": Config.MIN_QUESTION_LENGTH,
            "cache_size": Config.CACHE_SIZE
        }
    })

@app.route("/metrics", methods=["GET"])
@login_required
def get_metrics():
    """Endpoint para métricas del sistema"""
    documentos_indexados = 0
    if motor_busqueda.esta_inicializado() and hasattr(motor_busqueda, 'metadatos_unificados'):
        documentos_indexados = len(motor_busqueda.metadatos_unificados)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "metricas": monitor_rendimiento.obtener_metricas(),
        "estadisticas_sistema": {
            "auditorias_cargadas": len(DB_AUDITORIA),
            "total_registros": sum(len(db) for db in DB_AUDITORIA.values()),
            "tamaño_cache": len(cache_busqueda.cache),
            "motor_documentos_indexados": documentos_indexados
        }
    })

# =============================================================================
# MANEJO DE ERRORES GLOBAL MEJORADO
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    monitor_rendimiento.registrar_error("404_not_found")
    return jsonify({"success": False, "message": "Endpoint no encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    monitor_rendimiento.registrar_error("405_method_not_allowed")
    return jsonify({"success": False, "message": "Método no permitido"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error 500: {error}")
    monitor_rendimiento.registrar_error("500_internal_error")
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500

@app.errorhandler(413)
def too_large(error):
    monitor_rendimiento.registrar_error("413_payload_too_large")
    return jsonify({"success": False, "message": "Payload demasiado grande"}), 413

# =============================================================================
# INICIALIZACIÓN MEJORADA
# =============================================================================

if __name__ == "__main__":
    # Verificaciones de inicio mejoradas
    checks_passed = True

    if not DB_AUDITORIA:
        logger.error("❌ NO se puede iniciar: No hay bases de datos cargadas")
        checks_passed = False

    if not motor_busqueda.esta_inicializado():
        logger.warning("⚠️ Motor de búsqueda no pudo inicializarse correctamente")

    if checks_passed:
        logger.info("✅ Iniciando Auditel v2.1 - Análisis Normativo Inteligente")
        logger.info(f"📊 Bases cargadas: {list(DB_AUDITORIA.keys())}")
        
        documentos_indexados = 0
        if motor_busqueda.esta_inicializado() and hasattr(motor_busqueda, 'metadatos_unificados'):
            documentos_indexados = len(motor_busqueda.metadatos_unificados)
        
        logger.info(f"🔍 Motor de búsqueda: {documentos_indexados} documentos indexados")
        logger.info(f"💾 Cache inicializado: {cache_busqueda.estadisticas()}")

        debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        app.run(host="0.0.0.0", port=PORT, debug=debug_mode)
    else:
        logger.error("❌ No se pudo iniciar la aplicación debido a errores de configuración")
        exit(1)
