"""
Modelos de datos para normativas
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Normativa:
    """Modelo de una normativa o documento legal"""

    titulo: str
    contenido: str
    fecha_publicacion: Optional[datetime] = None
    url: Optional[str] = None
    tipo: str = "general"
    fuente: str = "local"
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    relevancia: float = 0.0
    fecha_scraping: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convierte la normativa a diccionario"""
        return {
            "titulo": self.titulo,
            "contenido": self.contenido,
            "fecha_publicacion": self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
            "url": self.url,
            "tipo": self.tipo,
            "fuente": self.fuente,
            "keywords": self.keywords,
            "metadata": self.metadata,
            "relevancia": self.relevancia,
            "fecha_scraping": self.fecha_scraping.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Normativa':
        """Crea una normativa desde un diccionario"""
        # Convertir fechas si existen
        if data.get("fecha_publicacion"):
            try:
                data["fecha_publicacion"] = datetime.fromisoformat(data["fecha_publicacion"])
            except (ValueError, TypeError):
                data["fecha_publicacion"] = None

        if data.get("fecha_scraping"):
            try:
                data["fecha_scraping"] = datetime.fromisoformat(data["fecha_scraping"])
            except (ValueError, TypeError):
                data["fecha_scraping"] = datetime.now()

        return cls(**data)

    def __str__(self) -> str:
        return f"Normativa({self.titulo[:50]}... | {self.fuente} | {self.tipo})"


@dataclass
class ResultadoBusqueda:
    """Resultado de búsqueda con normativas encontradas"""

    query: str
    normativas: List[Normativa] = field(default_factory=list)
    total_encontrado: int = 0
    fuentes_consultadas: List[str] = field(default_factory=list)
    tiempo_busqueda: float = 0.0
    desde_cache: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario"""
        return {
            "query": self.query,
            "normativas": [n.to_dict() for n in self.normativas],
            "total_encontrado": self.total_encontrado,
            "fuentes_consultadas": self.fuentes_consultadas,
            "tiempo_busqueda": self.tiempo_busqueda,
            "desde_cache": self.desde_cache,
            "timestamp": self.timestamp.isoformat()
        }

    def ordenar_por_relevancia(self):
        """Ordena las normativas por relevancia"""
        self.normativas.sort(key=lambda x: x.relevancia, reverse=True)

    def limitar_resultados(self, max_resultados: int = 10):
        """Limita el número de resultados"""
        self.normativas = self.normativas[:max_resultados]
        self.total_encontrado = len(self.normativas)
