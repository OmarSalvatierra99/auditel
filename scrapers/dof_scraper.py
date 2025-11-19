"""
Scraper para el Diario Oficial de la Federación (DOF)
"""
import re
import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper
from models.normativa import Normativa
from config.settings import Config

logger = logging.getLogger('auditel.scraper.dof')


class DOFScraper(BaseScraper):
    """Scraper específico para el Diario Oficial de la Federación"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = Config.DOF_BASE_URL
        self.search_url = Config.DOF_SEARCH_URL

    def buscar(self, query: str, max_resultados: int = 10, **kwargs) -> List[Normativa]:
        """
        Busca normativas en el DOF

        Args:
            query: Término de búsqueda
            max_resultados: Número máximo de resultados
            **kwargs: Parámetros adicionales (fecha_inicio, fecha_fin, seccion)

        Returns:
            Lista de normativas encontradas
        """
        normativas = []

        try:
            # Preparar parámetros de búsqueda
            params = {
                'q': query,
                'num': max_resultados
            }

            # Agregar filtros opcionales
            if 'fecha_inicio' in kwargs:
                params['fecha_inicio'] = kwargs['fecha_inicio']
            if 'fecha_fin' in kwargs:
                params['fecha_fin'] = kwargs['fecha_fin']

            logger.info(f"Buscando en DOF: '{query}' (max: {max_resultados})")

            # Realizar petición
            response = self._hacer_peticion(self.search_url, params=params)
            if not response:
                logger.warning("No se pudo obtener respuesta del DOF")
                return normativas

            # Parsear HTML
            soup = self._parsear_html(response.text)
            if not soup:
                return normativas

            # Extraer resultados
            # Nota: Los selectores pueden cambiar según la estructura del sitio
            resultados = self._extraer_resultados(soup)

            for resultado in resultados[:max_resultados]:
                normativa = self._parsear_resultado(resultado)
                if normativa:
                    normativas.append(normativa)

            logger.info(f"DOF: {len(normativas)} normativas encontradas")

        except Exception as e:
            logger.error(f"Error buscando en DOF: {e}", exc_info=True)

        return normativas

    def _extraer_resultados(self, soup) -> List:
        """Extrae elementos de resultado del HTML"""
        resultados = []

        try:
            # Intentar diferentes selectores comunes
            selectores = [
                'div.resultado-busqueda',
                'div.resultado',
                'div.documento',
                'article.resultado',
                'div[class*="result"]',
                'li.resultado'
            ]

            for selector in selectores:
                elementos = soup.select(selector)
                if elementos:
                    logger.debug(f"Encontrados {len(elementos)} con selector: {selector}")
                    resultados = elementos
                    break

            # Si no se encontraron con selectores, buscar por estructura
            if not resultados:
                # Buscar divs que contengan palabras clave de normativas
                todos_divs = soup.find_all('div')
                for div in todos_divs:
                    texto = div.get_text()
                    if any(keyword in texto.lower() for keyword in ['ley', 'decreto', 'acuerdo', 'artículo', 'reglamento']):
                        resultados.append(div)

        except Exception as e:
            logger.error(f"Error extrayendo resultados: {e}")

        return resultados

    def _parsear_resultado(self, elemento) -> Optional[Normativa]:
        """Parsea un elemento de resultado y crea una Normativa"""
        try:
            # Extraer título
            titulo = self._extraer_titulo(elemento)
            if not titulo:
                return None

            # Extraer contenido/descripción
            contenido = self._extraer_contenido(elemento)

            # Extraer URL
            url = self._extraer_url(elemento)

            # Extraer fecha
            fecha = self._extraer_fecha(elemento)

            # Extraer keywords
            texto_completo = f"{titulo} {contenido}"
            keywords = self.text_processor.extraer_keywords(texto_completo, max_keywords=8)

            # Extraer referencias legales
            referencias = self.text_processor.extraer_referencias_legales(texto_completo)

            normativa = Normativa(
                titulo=titulo,
                contenido=self._limpiar_texto(contenido),
                fecha_publicacion=fecha,
                url=url,
                tipo="dof",
                fuente="Diario Oficial de la Federación",
                keywords=keywords,
                metadata={
                    "referencias_legales": referencias,
                    "fuente_url": self.base_url
                }
            )

            return normativa

        except Exception as e:
            logger.error(f"Error parseando resultado: {e}")
            return None

    def _extraer_titulo(self, elemento) -> Optional[str]:
        """Extrae el título del elemento"""
        selectores_titulo = ['h3', 'h4', 'h2', '.titulo', 'strong', 'b']

        for selector in selectores_titulo:
            titulo_elem = elemento.select_one(selector)
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)
                if len(titulo) > 10:  # Validar que sea un título válido
                    return self._limpiar_texto(titulo)

        # Fallback: tomar primeras palabras del texto
        texto = elemento.get_text(strip=True)
        if texto:
            primeras_palabras = ' '.join(texto.split()[:20])
            return self._limpiar_texto(primeras_palabras)

        return None

    def _extraer_contenido(self, elemento) -> str:
        """Extrae el contenido/descripción del elemento"""
        # Intentar extraer de párrafos
        parrafos = elemento.find_all('p')
        if parrafos:
            contenido = ' '.join(p.get_text(strip=True) for p in parrafos)
            return self._limpiar_texto(contenido)[:1000]

        # Fallback: texto completo del elemento
        texto = elemento.get_text(strip=True)
        return self._limpiar_texto(texto)[:1000]

    def _extraer_url(self, elemento) -> Optional[str]:
        """Extrae la URL del documento"""
        # Buscar enlaces
        enlace = elemento.find('a', href=True)
        if enlace:
            href = enlace['href']
            # Convertir a URL absoluta si es relativa
            if href.startswith('http'):
                return href
            else:
                return urljoin(self.base_url, href)

        return None

    def _extraer_fecha(self, elemento) -> Optional[datetime]:
        """Extrae la fecha de publicación"""
        # Buscar en elementos comunes de fecha
        selectores_fecha = ['.fecha', 'time', 'span.date', '.fecha-publicacion']

        for selector in selectores_fecha:
            fecha_elem = elemento.select_one(selector)
            if fecha_elem:
                texto_fecha = fecha_elem.get_text(strip=True)
                fecha = self._parsear_fecha_texto(texto_fecha)
                if fecha:
                    return fecha

        # Buscar en el texto completo
        texto = elemento.get_text()
        fechas = self.text_processor.extraer_fechas(texto)
        if fechas:
            return fechas[0]

        return None

    def _parsear_fecha_texto(self, texto: str) -> Optional[datetime]:
        """Parsea texto de fecha a datetime"""
        # Intentar diferentes formatos
        formatos = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d de %B de %Y',
            '%d/%m/%y'
        ]

        for formato in formatos:
            try:
                return datetime.strptime(texto, formato)
            except ValueError:
                continue

        # Intentar extraer con regex
        fechas = self.text_processor.extraer_fechas(texto)
        if fechas:
            return fechas[0]

        return None

    def obtener_detalle(self, url: str) -> Optional[Normativa]:
        """
        Obtiene el detalle completo de una normativa desde su URL

        Args:
            url: URL del documento

        Returns:
            Normativa con información detallada
        """
        try:
            logger.info(f"Obteniendo detalle de: {url}")

            response = self._hacer_peticion(url)
            if not response:
                return None

            soup = self._parsear_html(response.text)
            if not soup:
                return None

            # Extraer título
            titulo_elem = soup.select_one('h1, h2, .titulo-documento')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else "Sin título"

            # Extraer contenido principal
            contenido_elem = soup.select_one('.contenido-documento, article, .documento')
            if contenido_elem:
                contenido = contenido_elem.get_text(separator='\n', strip=True)
            else:
                contenido = soup.get_text(separator='\n', strip=True)

            # Limpiar contenido
            contenido = self._limpiar_texto(contenido)

            # Extraer fecha
            fecha = None
            fecha_elem = soup.select_one('.fecha, time')
            if fecha_elem:
                fecha = self._parsear_fecha_texto(fecha_elem.get_text(strip=True))

            # Extraer keywords y referencias
            keywords = self.text_processor.extraer_keywords(contenido, max_keywords=15)
            referencias = self.text_processor.extraer_referencias_legales(contenido)

            normativa = Normativa(
                titulo=titulo,
                contenido=contenido[:5000],  # Limitar tamaño
                fecha_publicacion=fecha,
                url=url,
                tipo="dof_detalle",
                fuente="Diario Oficial de la Federación",
                keywords=keywords,
                metadata={
                    "referencias_legales": referencias,
                    "fuente_url": self.base_url,
                    "contenido_completo": len(contenido) > 5000
                }
            )

            return normativa

        except Exception as e:
            logger.error(f"Error obteniendo detalle de {url}: {e}", exc_info=True)
            return None
