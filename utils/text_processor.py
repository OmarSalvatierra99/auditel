"""
Utilidades para procesamiento de texto
"""
import re
from typing import List, Set
from datetime import datetime


class TextProcessor:
    """Procesador de texto para normalización y extracción"""

    # Palabras vacías en español
    STOP_WORDS = {
        'el', 'la', 'de', 'en', 'y', 'o', 'un', 'una', 'es', 'son',
        'por', 'para', 'con', 'sin', 'sobre', 'entre', 'hasta', 'desde',
        'los', 'las', 'del', 'al', 'a', 'ante', 'bajo', 'cabe', 'contra',
        'durante', 'mediante', 'según', 'tras', 'versus', 'vía'
    }

    @staticmethod
    def limpiar_texto(texto: str) -> str:
        """Limpia y normaliza texto"""
        if not texto:
            return ""

        # Eliminar caracteres de control
        texto = re.sub(r'[\x00-\x1F\x7F]', '', texto)

        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto)

        # Eliminar espacios al inicio y final
        return texto.strip()

    @staticmethod
    def sanitizar_html(texto: str) -> str:
        """Elimina tags HTML del texto"""
        # Eliminar scripts y styles
        texto = re.sub(r'<script[^>]*>.*?</script>', '', texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'<style[^>]*>.*?</style>', '', texto, flags=re.DOTALL | re.IGNORECASE)

        # Eliminar tags HTML
        texto = re.sub(r'<[^>]+>', ' ', texto)

        # Decodificar entidades HTML comunes
        entidades = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&aacute;': 'á',
            '&eacute;': 'é',
            '&iacute;': 'í',
            '&oacute;': 'ó',
            '&uacute;': 'ú',
            '&ntilde;': 'ñ',
            '&Aacute;': 'Á',
            '&Eacute;': 'É',
            '&Iacute;': 'Í',
            '&Oacute;': 'Ó',
            '&Uacute;': 'Ú',
            '&Ntilde;': 'Ñ'
        }

        for entidad, caracter in entidades.items():
            texto = texto.replace(entidad, caracter)

        return TextProcessor.limpiar_texto(texto)

    @staticmethod
    def extraer_keywords(texto: str, max_keywords: int = 10) -> List[str]:
        """Extrae palabras clave del texto"""
        if not texto:
            return []

        # Convertir a minúsculas
        texto = texto.lower()

        # Extraer palabras
        palabras = re.findall(r'\b\w+\b', texto)

        # Filtrar palabras vacías y muy cortas
        keywords = [
            p for p in palabras
            if p not in TextProcessor.STOP_WORDS and len(p) > 3
        ]

        # Contar frecuencias
        from collections import Counter
        frecuencias = Counter(keywords)

        # Retornar las más frecuentes
        return [palabra for palabra, _ in frecuencias.most_common(max_keywords)]

    @staticmethod
    def extraer_referencias_legales(texto: str) -> List[str]:
        """Extrae referencias a leyes, artículos, etc."""
        if not texto:
            return []

        patrones = [
            r'Ley\s+(?:de|del|sobre|para)\s+[\w\s]+(?=\.|,|\n|$)',
            r'Reglamento\s+(?:de|del|para)\s+[\w\s]+(?=\.|,|\n|$)',
            r'Artículo\s+\d+(?:\s+(?:bis|ter|quater|quinquies))?(?:\s+fracción\s+[IVXLCDM]+)?',
            r'NOM-\d+-[\w]+-\d+',
            r'Decreto\s+(?:por\s+el\s+que|que\s+establece|mediante\s+el\s+cual)[\w\s]+',
            r'Acuerdo\s+[\w\s]+(?=\.|,|\n|$)',
            r'Código\s+(?:Civil|Penal|Fiscal|de\s+Comercio)[\w\s]*',
            r'Constitución\s+Política[\w\s]*'
        ]

        referencias = []
        for patron in patrones:
            matches = re.findall(patron, texto, re.IGNORECASE)
            referencias.extend(matches)

        # Limpiar y deduplicar
        referencias = [TextProcessor.limpiar_texto(ref) for ref in referencias]
        return list(set(referencias))

    @staticmethod
    def extraer_fechas(texto: str) -> List[datetime]:
        """Extrae fechas del texto"""
        fechas = []

        # Patrón: DD/MM/YYYY o DD-MM-YYYY
        patron_fecha1 = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'
        matches = re.findall(patron_fecha1, texto)

        for match in matches:
            try:
                dia, mes, año = map(int, match)
                fecha = datetime(año, mes, dia)
                fechas.append(fecha)
            except ValueError:
                continue

        # Patrón: DD de mes de YYYY
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        patron_fecha2 = r'\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b'
        matches = re.findall(patron_fecha2, texto.lower())

        for match in matches:
            try:
                dia, mes_texto, año = match
                mes = meses.get(mes_texto.lower())
                if mes:
                    fecha = datetime(int(año), mes, int(dia))
                    fechas.append(fecha)
            except (ValueError, KeyError):
                continue

        return fechas

    @staticmethod
    def resumen_texto(texto: str, max_length: int = 300) -> str:
        """Genera un resumen del texto"""
        if not texto:
            return ""

        # Limpiar texto
        texto = TextProcessor.limpiar_texto(texto)

        # Si el texto es corto, retornarlo completo
        if len(texto) <= max_length:
            return texto

        # Truncar por oraciones completas
        oraciones = re.split(r'[.!?]+', texto)
        resumen = ""

        for oracion in oraciones:
            if len(resumen) + len(oracion) <= max_length:
                resumen += oracion + ". "
            else:
                break

        # Si no se agregó ninguna oración, truncar
        if not resumen:
            resumen = texto[:max_length] + "..."

        return resumen.strip()

    @staticmethod
    def normalizar_consulta(consulta: str) -> str:
        """Normaliza una consulta de búsqueda"""
        # Limpiar
        consulta = TextProcessor.limpiar_texto(consulta)

        # Convertir a minúsculas
        consulta = consulta.lower()

        # Eliminar caracteres especiales excepto espacios
        consulta = re.sub(r'[^\w\s]', ' ', consulta)

        # Normalizar espacios
        consulta = re.sub(r'\s+', ' ', consulta)

        return consulta.strip()
