"""
Gestor centralizado de scrapers
"""
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.dof_scraper import DOFScraper
from scrapers.tlaxcala_scraper import TlaxcalaScraper
from models.normativa import Normativa, ResultadoBusqueda
from utils.cache_manager import CacheManager
import time

logger = logging.getLogger('auditel.scraper_manager')


class ScraperManager:
    """Gestor que coordina múltiples scrapers"""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        self.scrapers = {
            'dof': DOFScraper(cache_manager=self.cache_manager),
            'tlaxcala': TlaxcalaScraper(cache_manager=self.cache_manager)
        }
        logger.info(f"ScraperManager inicializado con {len(self.scrapers)} scrapers")

    def buscar_en_todos(
        self,
        query: str,
        max_resultados_por_fuente: int = 5,
        usar_cache: bool = True,
        fuentes: Optional[List[str]] = None
    ) -> ResultadoBusqueda:
        """
        Busca en todas las fuentes en paralelo

        Args:
            query: Término de búsqueda
            max_resultados_por_fuente: Máximo de resultados por fuente
            usar_cache: Si usar caché o no
            fuentes: Lista de fuentes específicas (por defecto todas)

        Returns:
            ResultadoBusqueda con normativas de todas las fuentes
        """
        inicio = time.time()
        todas_normativas = []
        fuentes_consultadas = []

        # Determinar qué scrapers usar
        scrapers_activos = fuentes if fuentes else list(self.scrapers.keys())

        logger.info(f"Buscando '{query}' en fuentes: {scrapers_activos}")

        # Buscar en paralelo
        with ThreadPoolExecutor(max_workers=len(scrapers_activos)) as executor:
            # Crear tareas para cada scraper
            futuras = {}
            for nombre_fuente in scrapers_activos:
                scraper = self.scrapers.get(nombre_fuente)
                if scraper:
                    if usar_cache:
                        futura = executor.submit(
                            scraper.buscar_con_cache,
                            query,
                            max_resultados=max_resultados_por_fuente
                        )
                    else:
                        futura = executor.submit(
                            scraper.buscar,
                            query,
                            max_resultados=max_resultados_por_fuente
                        )
                    futuras[futura] = nombre_fuente

            # Recopilar resultados
            for futura in as_completed(futuras):
                nombre_fuente = futuras[futura]
                try:
                    resultados = futura.result(timeout=30)
                    if resultados:
                        todas_normativas.extend(resultados)
                        fuentes_consultadas.append(nombre_fuente)
                        logger.info(f"✅ {nombre_fuente}: {len(resultados)} resultados")
                    else:
                        logger.warning(f"⚠️ {nombre_fuente}: sin resultados")
                except Exception as e:
                    logger.error(f"❌ Error en {nombre_fuente}: {e}")

        tiempo_total = time.time() - inicio

        # Crear resultado
        resultado = ResultadoBusqueda(
            query=query,
            normativas=todas_normativas,
            total_encontrado=len(todas_normativas),
            fuentes_consultadas=fuentes_consultadas,
            tiempo_busqueda=tiempo_total,
            desde_cache=usar_cache
        )

        # Ordenar por relevancia
        resultado.ordenar_por_relevancia()

        logger.info(
            f"Búsqueda completada: {len(todas_normativas)} normativas "
            f"de {len(fuentes_consultadas)} fuentes en {tiempo_total:.2f}s"
        )

        return resultado

    def buscar_en_fuente(
        self,
        fuente: str,
        query: str,
        max_resultados: int = 10,
        usar_cache: bool = True
    ) -> List[Normativa]:
        """
        Busca en una fuente específica

        Args:
            fuente: Nombre de la fuente ('dof', 'tlaxcala')
            query: Término de búsqueda
            max_resultados: Máximo de resultados
            usar_cache: Si usar caché

        Returns:
            Lista de normativas encontradas
        """
        scraper = self.scrapers.get(fuente)
        if not scraper:
            logger.error(f"Fuente no encontrada: {fuente}")
            return []

        try:
            if usar_cache:
                return scraper.buscar_con_cache(query, max_resultados=max_resultados)
            else:
                return scraper.buscar(query, max_resultados=max_resultados)
        except Exception as e:
            logger.error(f"Error buscando en {fuente}: {e}")
            return []

    def obtener_detalle(self, fuente: str, url: str) -> Optional[Normativa]:
        """
        Obtiene el detalle de una normativa

        Args:
            fuente: Nombre de la fuente
            url: URL del documento

        Returns:
            Normativa con detalle completo
        """
        scraper = self.scrapers.get(fuente)
        if not scraper:
            logger.error(f"Fuente no encontrada: {fuente}")
            return None

        try:
            return scraper.obtener_detalle(url)
        except Exception as e:
            logger.error(f"Error obteniendo detalle de {url}: {e}")
            return None

    def limpiar_cache(self) -> bool:
        """Limpia el caché de todos los scrapers"""
        try:
            self.cache_manager.limpiar_todo()
            logger.info("Caché limpiado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return False

    def estadisticas_cache(self) -> Dict:
        """Obtiene estadísticas del caché"""
        return self.cache_manager.estadisticas()

    def cerrar_todos(self):
        """Cierra todas las sesiones de scrapers"""
        for nombre, scraper in self.scrapers.items():
            try:
                scraper.cerrar_sesion()
                logger.debug(f"Sesión cerrada: {nombre}")
            except Exception as e:
                logger.error(f"Error cerrando {nombre}: {e}")

    def __enter__(self):
        """Soporte para context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpieza al salir del context manager"""
        self.cerrar_todos()


# Singleton global
_scraper_manager_instance = None


def get_scraper_manager(cache_manager: Optional[CacheManager] = None) -> ScraperManager:
    """Obtiene instancia singleton del ScraperManager"""
    global _scraper_manager_instance
    if _scraper_manager_instance is None:
        _scraper_manager_instance = ScraperManager(cache_manager)
    return _scraper_manager_instance
