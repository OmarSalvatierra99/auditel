"""
Configuración centralizada para Auditel
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración centralizada de la aplicación"""

    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-por-defecto-cambiar-en-produccion")
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
    TOP_N_RESULTS = 6

    # Web Scraping
    SCRAPER_TIMEOUT = 30  # segundos
    SCRAPER_RETRY_ATTEMPTS = 3
    SCRAPER_DELAY = 1  # segundo entre peticiones
    CACHE_EXPIRATION = 86400  # 24 horas en segundos
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Directorios
    DATA_DIR = "data"
    CACHE_DIR = "cache_data"
    LOG_DIR = "logs"

    # Fuentes de datos
    DOF_BASE_URL = "https://www.dof.gob.mx"
    DOF_SEARCH_URL = "https://www.dof.gob.mx/busqueda_avanzada.php"
    TLAXCALA_PERIODICO_URL = "https://periodico.tlaxcala.gob.mx/index.php/buscar"
    DIPUTADOS_LEYES_URL = "http://www.diputados.gob.mx/LeyesBiblio/index.htm"


class AuditoriaConfig:
    """Configuración de tipos de auditorías"""

    TIPOS = {
        "Obra Pública": {
            "archivo": "obra_publica.json",
            "descripcion": "Análisis de normativas de construcción, licitaciones y contratación pública",
            "campos_normativas": [
                "normatividad_local_administracion_directa",
                "normatividad_local_contrato",
                "normatividad_federal_administracion_directa",
                "normatividad_federal_contratacion"
            ],
            "keywords_scraping": [
                "obras públicas",
                "licitación",
                "contratación pública",
                "construcción",
                "infraestructura"
            ]
        },
        "Financiera": {
            "archivo": "financiero.json",
            "descripcion": "Análisis de normativas contables, presupuestales y de control financiero",
            "campos_normativas": [
                "normatividad_local",
                "normatividad_federal"
            ],
            "keywords_scraping": [
                "contabilidad gubernamental",
                "presupuesto",
                "fiscalización",
                "control interno",
                "gasto público"
            ]
        }
    }


class ScraperConfig:
    """Configuración específica para scrapers"""

    # Headers para peticiones HTTP
    HEADERS = {
        "User-Agent": Config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    # Patrones de búsqueda para normativas
    NORMATIVA_PATTERNS = [
        r"Ley\s+(?:de|del|sobre)\s+[\w\s]+",
        r"Reglamento\s+(?:de|del)\s+[\w\s]+",
        r"Artículo\s+\d+",
        r"NOM-\d+-[\w]+-\d+",
        r"Decreto\s+(?:por\s+el\s+que|que\s+establece)",
        r"Acuerdo\s+[\w\s]+"
    ]

    # Selectores CSS para diferentes sitios
    DOF_SELECTORS = {
        "resultados": "div.resultado-busqueda",
        "titulo": "h3.titulo-documento",
        "fecha": "span.fecha",
        "contenido": "div.contenido-documento",
        "link": "a.ver-documento"
    }

    TLAXCALA_SELECTORS = {
        "resultados": "div.resultado",
        "titulo": "h4",
        "fecha": "span.fecha-publicacion",
        "contenido": "div.extracto",
        "link": "a.enlace-documento"
    }
