"""
Clase base para scrapers
"""
import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

from config.settings import ScraperConfig, Config
from models.normativa import Normativa
from utils.text_processor import TextProcessor
from utils.cache_manager import CacheManager

logger = logging.getLogger('auditel.scraper')


class BaseScraper(ABC):
    """Clase base abstracta para todos los scrapers"""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.session = requests.Session()
        self.session.headers.update(ScraperConfig.HEADERS)
        self.text_processor = TextProcessor()
        self.cache_manager = cache_manager or CacheManager()
        self.timeout = Config.SCRAPER_TIMEOUT
        self.retry_attempts = Config.SCRAPER_RETRY_ATTEMPTS
        self.delay = Config.SCRAPER_DELAY

    def _hacer_peticion(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Realiza una petición HTTP con reintentos"""
        for intento in range(self.retry_attempts):
            try:
                logger.debug(f"Petición a {url} (intento {intento + 1}/{self.retry_attempts})")

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    allow_redirects=True
                )

                response.raise_for_status()

                # Delay entre peticiones
                if self.delay > 0:
                    time.sleep(self.delay)

                return response

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en {url} (intento {intento + 1})")
                if intento < self.retry_attempts - 1:
                    time.sleep(2 ** intento)  # Backoff exponencial
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Error en petición a {url}: {e}")
                if intento < self.retry_attempts - 1:
                    time.sleep(2 ** intento)
                    continue
                return None

        logger.error(f"Falló petición a {url} después de {self.retry_attempts} intentos")
        return None

    def _parsear_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """Parsea contenido HTML con BeautifulSoup"""
        try:
            return BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            logger.error(f"Error parseando HTML: {e}")
            try:
                # Fallback a html.parser
                return BeautifulSoup(html_content, 'html.parser')
            except Exception as e2:
                logger.error(f"Error con fallback parser: {e2}")
                return None

    def _limpiar_texto(self, texto: str) -> str:
        """Limpia y normaliza texto extraído"""
        return self.text_processor.sanitizar_html(texto)

    @abstractmethod
    def buscar(self, query: str, **kwargs) -> List[Normativa]:
        """Método abstracto para buscar normativas"""
        pass

    @abstractmethod
    def obtener_detalle(self, url: str) -> Optional[Normativa]:
        """Método abstracto para obtener detalle de una normativa"""
        pass

    def _generar_cache_key(self, query: str, **kwargs) -> str:
        """Genera una clave única para caché"""
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{self.__class__.__name__}_{query}_{params}"

    def buscar_con_cache(self, query: str, **kwargs) -> List[Normativa]:
        """Busca con caché activado"""
        cache_key = self._generar_cache_key(query, **kwargs)

        # Intentar obtener de caché
        cached_data = self.cache_manager.obtener(cache_key)
        if cached_data:
            logger.info(f"Resultados obtenidos de caché para: {query}")
            return [Normativa.from_dict(n) for n in cached_data]

        # Buscar en la web
        logger.info(f"Buscando en web: {query}")
        resultados = self.buscar(query, **kwargs)

        # Guardar en caché
        if resultados:
            datos_cache = [n.to_dict() for n in resultados]
            self.cache_manager.guardar(cache_key, datos_cache)

        return resultados

    def cerrar_sesion(self):
        """Cierra la sesión de requests"""
        self.session.close()

    def __enter__(self):
        """Soporte para context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpieza al salir del context manager"""
        self.cerrar_sesion()
