"""
Scraper para el Periódico Oficial del Estado de Tlaxcala
"""
import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin, quote

from scrapers.base_scraper import BaseScraper
from models.normativa import Normativa
from config.settings import Config

logger = logging.getLogger('auditel.scraper.tlaxcala')


class TlaxcalaScraper(BaseScraper):
    """Scraper específico para el Periódico Oficial del Estado de Tlaxcala"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://periodico.tlaxcala.gob.mx"
        self.search_url = Config.TLAXCALA_PERIODICO_URL

    def buscar(self, query: str, max_resultados: int = 10, **kwargs) -> List[Normativa]:
        """
        Busca normativas en el Periódico Oficial de Tlaxcala

        Args:
            query: Término de búsqueda
            max_resultados: Número máximo de resultados
            **kwargs: Parámetros adicionales

        Returns:
            Lista de normativas encontradas
        """
        normativas = []

        try:
            # Preparar parámetros de búsqueda
            params = {
                'buscar': query,
                'ordenar': 'fecha_desc'
            }

            logger.info(f"Buscando en Periódico Oficial Tlaxcala: '{query}'")

            # Realizar petición
            response = self._hacer_peticion(self.search_url, params=params)
            if not response:
                logger.warning("No se pudo obtener respuesta del Periódico Oficial")
                return normativas

            # Parsear HTML
            soup = self._parsear_html(response.text)
            if not soup:
                return normativas

            # Extraer resultados
            resultados = self._extraer_resultados(soup)

            for resultado in resultados[:max_resultados]:
                normativa = self._parsear_resultado(resultado)
                if normativa:
                    normativas.append(normativa)

            logger.info(f"Periódico Oficial Tlaxcala: {len(normativas)} normativas encontradas")

        except Exception as e:
            logger.error(f"Error buscando en Periódico Oficial: {e}", exc_info=True)

        return normativas

    def _extraer_resultados(self, soup) -> List:
        """Extrae elementos de resultado del HTML"""
        resultados = []

        try:
            # Selectores específicos para el sitio de Tlaxcala
            selectores = [
                'div.resultado',
                'div.documento',
                'tr.resultado',
                'div[class*="result"]',
                'article',
                '.item-resultado'
            ]

            for selector in selectores:
                elementos = soup.select(selector)
                if elementos:
                    logger.debug(f"Encontrados {len(elementos)} con selector: {selector}")
                    resultados = elementos
                    break

            # Fallback: buscar en tablas (formato común en periódicos oficiales)
            if not resultados:
                tablas = soup.find_all('table')
                for tabla in tablas:
                    filas = tabla.find_all('tr')
                    if filas and len(filas) > 1:  # Tiene header
                        resultados = filas[1:]  # Excluir header
                        break

            # Si no hay resultados, buscar divs con contenido legal
            if not resultados:
                todos_divs = soup.find_all('div')
                for div in todos_divs:
                    texto = div.get_text()
                    if any(keyword in texto.lower() for keyword in
                          ['decreto', 'ley', 'reglamento', 'acuerdo', 'periódico oficial']):
                        if len(texto) > 100:  # Filtrar divs muy pequeños
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

            # Extraer número de periódico si existe
            numero_periodico = self._extraer_numero_periodico(elemento)

            # Extraer keywords
            texto_completo = f"{titulo} {contenido}"
            keywords = self.text_processor.extraer_keywords(texto_completo, max_keywords=8)

            # Extraer referencias legales
            referencias = self.text_processor.extraer_referencias_legales(texto_completo)

            # Metadata adicional
            metadata = {
                "referencias_legales": referencias,
                "fuente_url": self.base_url,
                "estado": "Tlaxcala"
            }

            if numero_periodico:
                metadata["numero_periodico"] = numero_periodico

            normativa = Normativa(
                titulo=titulo,
                contenido=self._limpiar_texto(contenido),
                fecha_publicacion=fecha,
                url=url,
                tipo="periodico_oficial_local",
                fuente="Periódico Oficial del Estado de Tlaxcala",
                keywords=keywords,
                metadata=metadata
            )

            return normativa

        except Exception as e:
            logger.error(f"Error parseando resultado: {e}")
            return None

    def _extraer_titulo(self, elemento) -> Optional[str]:
        """Extrae el título del elemento"""
        # Selectores comunes para título
        selectores_titulo = ['h3', 'h4', 'h2', 'h1', '.titulo', 'strong', 'b', 'td']

        for selector in selectores_titulo:
            titulo_elem = elemento.select_one(selector)
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)
                if len(titulo) > 10 and len(titulo) < 300:
                    return self._limpiar_texto(titulo)

        # Fallback: buscar en atributos
        if elemento.get('title'):
            return self._limpiar_texto(elemento['title'])

        # Último fallback: primeras palabras del texto
        texto = elemento.get_text(strip=True)
        if texto:
            primeras_palabras = ' '.join(texto.split()[:25])
            return self._limpiar_texto(primeras_palabras)

        return None

    def _extraer_contenido(self, elemento) -> str:
        """Extrae el contenido/descripción del elemento"""
        # Intentar extraer de párrafos
        parrafos = elemento.find_all('p')
        if parrafos:
            contenido = ' '.join(p.get_text(strip=True) for p in parrafos)
            return self._limpiar_texto(contenido)[:1000]

        # Intentar extraer de divs con clase "contenido" o similar
        contenido_elem = elemento.select_one('.contenido, .extracto, .resumen, .descripcion')
        if contenido_elem:
            return self._limpiar_texto(contenido_elem.get_text(strip=True))[:1000]

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

        # Buscar en atributos data-*
        if elemento.get('data-url'):
            return urljoin(self.base_url, elemento['data-url'])

        return None

    def _extraer_fecha(self, elemento) -> Optional[datetime]:
        """Extrae la fecha de publicación"""
        # Buscar en elementos comunes de fecha
        selectores_fecha = [
            '.fecha',
            'time',
            'span.date',
            '.fecha-publicacion',
            'td.fecha',
            '.date'
        ]

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

    def _extraer_numero_periodico(self, elemento) -> Optional[str]:
        """Extrae el número del periódico oficial"""
        texto = elemento.get_text()

        # Patrones comunes para número de periódico
        import re
        patrones = [
            r'N[úu]mero?\s+(\d+)',
            r'No\.\s*(\d+)',
            r'Núm\.\s*(\d+)',
            r'Tomo\s+[IVXLCDM]+\s+No\.\s*(\d+)'
        ]

        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1)

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
            titulo_elem = soup.select_one('h1, h2, .titulo-documento, .titulo')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else "Sin título"

            # Extraer contenido principal
            contenido_elem = soup.select_one('.contenido-documento, article, .documento, .texto-completo')
            if contenido_elem:
                contenido = contenido_elem.get_text(separator='\n', strip=True)
            else:
                contenido = soup.get_text(separator='\n', strip=True)

            # Limpiar contenido
            contenido = self._limpiar_texto(contenido)

            # Extraer fecha
            fecha = None
            fecha_elem = soup.select_one('.fecha, time, .fecha-publicacion')
            if fecha_elem:
                fecha = self._parsear_fecha_texto(fecha_elem.get_text(strip=True))

            # Extraer número de periódico
            numero_periodico = self._extraer_numero_periodico(soup)

            # Extraer keywords y referencias
            keywords = self.text_processor.extraer_keywords(contenido, max_keywords=15)
            referencias = self.text_processor.extraer_referencias_legales(contenido)

            metadata = {
                "referencias_legales": referencias,
                "fuente_url": self.base_url,
                "estado": "Tlaxcala",
                "contenido_completo": len(contenido) > 5000
            }

            if numero_periodico:
                metadata["numero_periodico"] = numero_periodico

            normativa = Normativa(
                titulo=titulo,
                contenido=contenido[:5000],  # Limitar tamaño
                fecha_publicacion=fecha,
                url=url,
                tipo="periodico_oficial_local_detalle",
                fuente="Periódico Oficial del Estado de Tlaxcala",
                keywords=keywords,
                metadata=metadata
            )

            return normativa

        except Exception as e:
            logger.error(f"Error obteniendo detalle de {url}: {e}", exc_info=True)
            return None
